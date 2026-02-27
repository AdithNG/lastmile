"""
Real-time rerouter.

When a traffic event is received for an active route, this service:
  1. Fetches the route's remaining stops from the DB.
  2. Rebuilds the distance/time matrix (with traffic delays applied).
  3. Recomputes ETAs for each remaining stop.
  4. Returns the updated stop sequence with new planned arrivals.

The updated payload is broadcast over WebSocket to the frontend.
"""

import logging
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.depot import Depot
from app.models.route import Route, RouteStop
from app.models.stop import Stop
from app.models.vehicle import Vehicle
from app.services.constraint_checker import time_to_minutes
from app.services.distance_matrix import build_distance_matrix, haversine_matrix

logger = logging.getLogger(__name__)


async def reroute_active(
    route_id: int,
    traffic_events: List[Dict],
    db: AsyncSession,
) -> Dict:
    """
    Recompute ETAs for an active route given a list of traffic events.

    Each traffic_event dict:
      { "from_idx": int, "to_idx": int, "delay_factor": float }

    delay_factor multiplies the travel time on that matrix edge.
    e.g. delay_factor=1.5 means 50% longer travel.
    """
    route = (await db.execute(select(Route).where(Route.id == route_id))).scalar_one()
    vehicle = (await db.execute(select(Vehicle).where(Vehicle.id == route.vehicle_id))).scalar_one()
    depot = (await db.execute(select(Depot).where(Depot.id == vehicle.depot_id))).scalar_one()

    route_stops_rows = (
        await db.execute(
            select(RouteStop)
            .where(RouteStop.route_id == route_id)
            .order_by(RouteStop.sequence)
        )
    ).scalars().all()

    stops = [
        (await db.execute(select(Stop).where(Stop.id == rs.stop_id))).scalar_one()
        for rs in route_stops_rows
    ]

    coords = [(depot.lat, depot.lng)] + [(s.lat, s.lng) for s in stops]

    try:
        if settings.ors_api_key:
            dist_matrix, time_matrix = await build_distance_matrix(coords)
        else:
            dist_matrix, time_matrix = haversine_matrix(coords)
    except Exception as exc:
        logger.warning("ORS unavailable during reroute (%s), using haversine", exc)
        dist_matrix, time_matrix = haversine_matrix(coords)

    # Apply traffic delay factors to the time matrix
    for event in traffic_events:
        fi = event.get("from_idx", 0)
        ti = event.get("to_idx", 0)
        factor = event.get("delay_factor", 1.5)
        if fi < len(time_matrix) and ti < len(time_matrix[fi]):
            time_matrix[fi][ti] *= factor

    # Recompute ETAs along the (unchanged) stop sequence
    current_time = 480.0  # default 8:00 AM; real system would use actual departure time
    current_pos = 0       # depot
    updated_stops = []

    for i, stop in enumerate(stops):
        matrix_idx = i + 1
        travel = time_matrix[current_pos][matrix_idx]
        arrival = current_time + travel
        earliest = time_to_minutes(stop.earliest_time)
        current_time = max(arrival, earliest)
        current_pos = matrix_idx

        # Convert minutes-since-midnight back to "HH:MM" for the response
        h, m = divmod(int(arrival), 60)
        updated_stops.append({
            "stop_id": stop.id,
            "sequence": i,
            "planned_arrival": f"{h:02d}:{m:02d}",
            "planned_arrival_min": round(arrival, 1),
            "lat": stop.lat,
            "lng": stop.lng,
        })

    return {
        "route_id": route_id,
        "rerouted": True,
        "stops": updated_stops,
    }
