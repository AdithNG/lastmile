"""
Simulation engine.

Generates a realistic delivery scenario (depot + stops + vehicles) for a
given city, then seeds the database so the optimizer can be called on it
immediately. This is what powers the live demo — no real drivers needed.
"""

import random
from datetime import time
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.depot import Depot
from app.models.stop import Stop
from app.models.vehicle import Vehicle

# Bounding boxes (lat_min, lat_max), (lng_min, lng_max) for demo cities
CITIES: Dict[str, Dict] = {
    "seattle": {"lat": (47.55, 47.72), "lng": (-122.45, -122.25)},
    "la":      {"lat": (33.90, 34.10), "lng": (-118.45, -118.20)},
    "nyc":     {"lat": (40.65, 40.80), "lng": (-74.05, -73.85)},
}

# Realistic delivery time windows (earliest, latest)
TIME_WINDOWS: List[tuple] = [
    (time(8, 0),  time(12, 0)),   # morning
    (time(10, 0), time(14, 0)),   # mid-morning
    (time(12, 0), time(16, 0)),   # afternoon
    (time(14, 0), time(18, 0)),   # late afternoon
]

VEHICLE_CAPACITIES = [200.0, 300.0, 500.0]


async def generate_scenario(
    city: str,
    num_stops: int,
    num_vehicles: int,
    seed: Optional[int],
    db: AsyncSession,
) -> Dict:
    """
    Create a depot, vehicles, and stops in the DB and return their IDs
    so the caller can immediately submit them to /routes/optimize.
    """
    rng = random.Random(seed)
    bounds = CITIES.get(city, CITIES["seattle"])

    depot_lat = (bounds["lat"][0] + bounds["lat"][1]) / 2
    depot_lng = (bounds["lng"][0] + bounds["lng"][1]) / 2

    depot = Depot(
        name=f"{city.title()} Distribution Center",
        lat=depot_lat,
        lng=depot_lng,
        open_time=time(6, 0),
        close_time=time(22, 0),
    )
    db.add(depot)
    await db.flush()

    vehicles: List[Vehicle] = []
    for i in range(num_vehicles):
        v = Vehicle(
            depot_id=depot.id,
            capacity_kg=rng.choice(VEHICLE_CAPACITIES),
            driver_name=f"Driver {i + 1}",
        )
        db.add(v)
        vehicles.append(v)
    await db.flush()

    stops: List[Stop] = []
    for i in range(num_stops):
        earliest, latest = rng.choice(TIME_WINDOWS)
        s = Stop(
            address=f"{rng.randint(100, 9999)} {rng.choice(['Main', 'Oak', 'Elm', 'Pine', 'Cedar'])} St, {city.title()}",
            lat=rng.uniform(*bounds["lat"]),
            lng=rng.uniform(*bounds["lng"]),
            earliest_time=earliest,
            latest_time=latest,
            package_weight_kg=round(rng.uniform(1.0, 30.0), 1),
        )
        db.add(s)
        stops.append(s)
    await db.flush()

    await db.commit()

    return {
        "depot_id": depot.id,
        "vehicle_ids": [v.id for v in vehicles],
        "stop_ids": [s.id for s in stops],
        "city": city,
        "num_stops": num_stops,
        "num_vehicles": num_vehicles,
    }


def inject_traffic_event(route_id: int, delay_factor: float = 1.5) -> Dict:
    """
    Build a synthetic traffic event payload.
    In a real system this would come from HERE Traffic or Google Maps.
    The frontend calls POST /simulation/inject-traffic, which triggers
    the rerouter and broadcasts the updated route over WebSocket.
    """
    return {
        "route_id": route_id,
        "delay_factor": delay_factor,
        "event": "traffic_injected",
    }
