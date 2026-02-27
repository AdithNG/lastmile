"""
Distance matrix builder.

Primary:  OpenRouteService Matrix API — returns real driving distances and
          travel times that account for road network topology.
Fallback: Haversine formula — straight-line distances with a fixed average
          speed assumption. Used in dev/test when ORS is unavailable.

Matrix layout: coords[0] is always the depot; coords[1..n] are stops.
Returns (distance_matrix_km, time_matrix_minutes) as nested lists.
"""

from typing import List, Tuple

import httpx
import numpy as np

from app.config import settings


async def build_distance_matrix(
    coords: List[Tuple[float, float]],
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Call OpenRouteService to build an NxN distance + time matrix.
    coords is a list of (lat, lng) tuples; ORS expects [lng, lat].
    Free tier: 2 000 requests/day, up to 50 locations per request.
    """
    locations = [[lng, lat] for lat, lng in coords]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openrouteservice.org/v2/matrix/driving-car",
            headers={
                "Authorization": settings.ors_api_key,
                "Content-Type": "application/json",
            },
            json={
                "locations": locations,
                "metrics": ["distance", "duration"],
                "units": "km",
            },
        )
        response.raise_for_status()
        data = response.json()

    distance_matrix: List[List[float]] = data["distances"]                     # km
    time_matrix: List[List[float]] = [[s / 60.0 for s in row] for row in data["durations"]]  # sec → min

    return distance_matrix, time_matrix


def haversine_matrix(
    coords: List[Tuple[float, float]],
    avg_speed_kmh: float = 30.0,
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Compute NxN great-circle distance matrix using the haversine formula.
    Travel time is estimated as distance / avg_speed_kmh * 60 (minutes).
    avg_speed_kmh=30 is a conservative urban delivery speed.
    """
    n = len(coords)
    R = 6371.0  # Earth radius in km

    lats = np.radians([c[0] for c in coords])
    lngs = np.radians([c[1] for c in coords])

    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        dlat = lats - lats[i]
        dlng = lngs - lngs[i]
        a = np.sin(dlat / 2) ** 2 + np.cos(lats[i]) * np.cos(lats) * np.sin(dlng / 2) ** 2
        dist[i] = 2 * R * np.arcsin(np.sqrt(a))

    time_min = (dist / avg_speed_kmh) * 60.0

    return dist.tolist(), time_min.tolist()
