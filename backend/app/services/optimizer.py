"""
CVRPTW Solver — Capacitated Vehicle Routing Problem with Time Windows.

Algorithm:
  Phase 1 — Greedy nearest-neighbor construction: O(n²) per vehicle.
             Builds a feasible (but not optimal) initial solution fast.
  Phase 2 — 2-opt local search improvement: iteratively reverses route
             sub-segments until no improving swap exists.
             Typically reduces total distance 10–20% over greedy alone.

This is the same class of heuristic used in Amazon's DDP (Dynamic Dispatch
Platform). Exact solvers become infeasible above ~50 stops; heuristics like
this get within 5–15% of optimal in seconds.
"""

import logging
from typing import List, Dict, Tuple

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.depot import Depot
from app.models.route import Route, RouteStop
from app.models.stop import Stop
from app.models.vehicle import Vehicle
from app.services.constraint_checker import time_to_minutes
from app.services.distance_matrix import build_distance_matrix, haversine_matrix
from app.config import settings

logger = logging.getLogger(__name__)


class CVRPTWSolver:
    """
    Solves the Capacitated Vehicle Routing Problem with Time Windows.

    Attributes:
        stops:      List of stop dicts with keys idx, weight, earliest_min, latest_min.
        vehicles:   List of vehicle dicts with keys id, capacity_kg, driver_name.
        dist:       NxN numpy distance matrix (km).
        time_m:     NxN numpy travel-time matrix (minutes).
        depot_idx:  Index of the depot in the distance/time matrices (always 0).
        start_min:  Dispatch time in minutes since midnight (default 8:00 AM = 480).
    """

    def __init__(
        self,
        stops: List[dict],
        vehicles: List[dict],
        dist_matrix: List[List[float]],
        time_matrix: List[List[float]],
        depot_idx: int = 0,
        start_min: float = 480.0,
    ):
        self.stops = stops
        self.vehicles = vehicles
        self.dist = np.array(dist_matrix, dtype=float)
        self.time_m = np.array(time_matrix, dtype=float)
        self.depot_idx = depot_idx
        self.start_min = start_min
        self.n = len(stops)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(self) -> List[Dict]:
        """Run full solve: greedy construction → 2-opt improvement."""
        routes = self._greedy()
        routes = [self._two_opt(r) for r in routes]
        return routes

    def score(self, routes: List[Dict]) -> Dict:
        total_dist = sum(r["dist"] for r in routes)
        total_stops = sum(len(r["stops"]) for r in routes)
        return {
            "total_distance_km": round(total_dist, 3),
            "num_routes": len(routes),
            "avg_stops_per_route": round(total_stops / max(len(routes), 1), 1),
            "unassigned": self.n - total_stops,
        }

    # ------------------------------------------------------------------
    # Phase 1: Greedy nearest-neighbor construction
    # ------------------------------------------------------------------

    def _greedy(self) -> List[Dict]:
        unassigned = list(range(self.n))
        routes: List[Dict] = []

        for vehicle in self.vehicles:
            if not unassigned:
                break

            route_stops: List[int] = []
            current_load = 0.0
            current_time = self.start_min
            current_pos = self.depot_idx

            while unassigned:
                best_i, best_dist = None, float("inf")

                for i in unassigned:
                    s = self.stops[i]

                    # Capacity check
                    if current_load + s["weight"] > vehicle["capacity_kg"]:
                        continue

                    # Time window feasibility check
                    travel = self.time_m[current_pos][s["idx"]]
                    if current_time + travel > s["latest_min"]:
                        continue

                    d = self.dist[current_pos][s["idx"]]
                    if d < best_dist:
                        best_dist, best_i = d, i

                if best_i is None:
                    break  # no feasible stop reachable — close this route

                s = self.stops[best_i]
                travel = self.time_m[current_pos][s["idx"]]
                current_time = max(current_time + travel, s["earliest_min"])
                current_load += s["weight"]
                current_pos = s["idx"]
                route_stops.append(best_i)
                unassigned.remove(best_i)

            if route_stops:
                routes.append({
                    "vehicle": vehicle,
                    "stops": route_stops,
                    "dist": self._route_dist(route_stops),
                })

        return routes

    # ------------------------------------------------------------------
    # Phase 2: 2-opt local search improvement
    # ------------------------------------------------------------------

    def _two_opt(self, route: Dict) -> Dict:
        """
        Iteratively try reversing every sub-segment [i+1 .. j] of the route.
        Accept the swap if it reduces total distance AND remains feasible.
        Stop when no improving swap is found (local optimum).
        """
        best = route["stops"][:]
        improved = True

        while improved:
            improved = False
            for i in range(len(best) - 1):
                for j in range(i + 2, len(best)):
                    candidate = best[: i + 1] + best[i + 1 : j + 1][::-1] + best[j + 1 :]
                    if self._route_dist(candidate) < self._route_dist(best) - 1e-6:
                        if self._feasible(candidate, route["vehicle"]):
                            best = candidate
                            improved = True

        return {**route, "stops": best, "dist": self._route_dist(best)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _route_dist(self, stop_indices: List[int]) -> float:
        """Total route distance including depot → first stop and last stop → depot."""
        if not stop_indices:
            return 0.0
        d = self.dist[self.depot_idx][self.stops[stop_indices[0]]["idx"]]
        for k in range(len(stop_indices) - 1):
            a = self.stops[stop_indices[k]]["idx"]
            b = self.stops[stop_indices[k + 1]]["idx"]
            d += self.dist[a][b]
        d += self.dist[self.stops[stop_indices[-1]]["idx"]][self.depot_idx]
        return float(d)

    def _feasible(self, stop_indices: List[int], vehicle: dict) -> bool:
        """Check capacity and time windows for a candidate route ordering."""
        if sum(self.stops[i]["weight"] for i in stop_indices) > vehicle["capacity_kg"]:
            return False
        t = self.start_min
        pos = self.depot_idx
        for i in stop_indices:
            s = self.stops[i]
            t = max(t + self.time_m[pos][s["idx"]], s["earliest_min"])
            if t > s["latest_min"]:
                return False
            pos = s["idx"]
        return True


# ------------------------------------------------------------------
# Service layer — called by the Celery task
# ------------------------------------------------------------------

async def run_optimization(
    depot_id: int,
    vehicle_ids: List[int],
    stop_ids: List[int],
    date_str: str,
    db: AsyncSession,
) -> Dict:
    from datetime import datetime

    depot = (await db.execute(select(Depot).where(Depot.id == depot_id))).scalar_one()
    vehicles_db = (await db.execute(select(Vehicle).where(Vehicle.id.in_(vehicle_ids)))).scalars().all()
    stops_db = (await db.execute(select(Stop).where(Stop.id.in_(stop_ids)))).scalars().all()

    # Depot is always index 0; stops are indices 1..n
    coords = [(depot.lat, depot.lng)] + [(s.lat, s.lng) for s in stops_db]

    try:
        if settings.ors_api_key:
            dist_matrix, time_matrix = await build_distance_matrix(coords)
        else:
            dist_matrix, time_matrix = haversine_matrix(coords)
    except Exception as exc:
        logger.warning("ORS unavailable (%s), falling back to haversine", exc)
        dist_matrix, time_matrix = haversine_matrix(coords)

    stops_data = [
        {
            "id": s.id,
            "idx": i + 1,
            "weight": s.package_weight_kg,
            "earliest_min": time_to_minutes(s.earliest_time),
            "latest_min": time_to_minutes(s.latest_time),
        }
        for i, s in enumerate(stops_db)
    ]
    vehicles_data = [
        {"id": v.id, "capacity_kg": v.capacity_kg, "driver_name": v.driver_name}
        for v in vehicles_db
    ]

    solver = CVRPTWSolver(stops_data, vehicles_data, dist_matrix, time_matrix, depot_idx=0)

    # Benchmark: record greedy-only distance before 2-opt
    greedy_routes = solver._greedy()
    greedy_total = sum(r["dist"] for r in greedy_routes)

    # Full solve
    optimized_routes = solver.solve()
    optimized_total = sum(r["dist"] for r in optimized_routes)
    improvement_pct = (
        (greedy_total - optimized_total) / greedy_total * 100 if greedy_total > 0 else 0
    )

    # Persist routes to DB
    route_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    db_route_ids: List[int] = []

    for route in optimized_routes:
        db_route = Route(
            vehicle_id=route["vehicle"]["id"],
            date=route_date,
            total_distance_km=route["dist"],
        )
        db.add(db_route)
        await db.flush()

        for seq, stop_i in enumerate(route["stops"]):
            db.add(RouteStop(
                route_id=db_route.id,
                stop_id=stops_data[stop_i]["id"],
                sequence=seq,
            ))

        db_route_ids.append(db_route.id)

    await db.commit()

    return {
        "route_ids": db_route_ids,
        "total_distance_km": round(optimized_total, 3),
        "greedy_distance_km": round(greedy_total, 3),
        "improvement_pct": round(improvement_pct, 2),
        "num_routes": len(optimized_routes),
        "score": solver.score(optimized_routes),
    }
