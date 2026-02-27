from datetime import time
from typing import List, Tuple


def time_to_minutes(t: time) -> float:
    """Convert a time object to minutes since midnight."""
    return t.hour * 60 + t.minute + t.second / 60


def check_time_window(arrival_min: float, earliest: time, latest: time) -> bool:
    """Return True if arrival falls within [earliest, latest]."""
    return time_to_minutes(earliest) <= arrival_min <= time_to_minutes(latest)


def check_capacity(weights: List[float], vehicle_capacity: float) -> bool:
    """Return True if total weight does not exceed vehicle capacity."""
    return sum(weights) <= vehicle_capacity


def validate_route(
    stops: List[dict],
    vehicle_capacity: float,
    dist_matrix: List[List[float]],
    time_matrix: List[List[float]],
    depot_idx: int,
    start_time_min: float = 480.0,
) -> Tuple[bool, List[float]]:
    """
    Validate a full route against capacity and time window constraints.

    Each stop dict must have keys: idx, weight, earliest_min, latest_min.
    Returns (is_valid, list_of_arrival_times_in_minutes).
    """
    if not check_capacity([s["weight"] for s in stops], vehicle_capacity):
        return False, []

    arrival_times: List[float] = []
    current_time = start_time_min
    current_pos = depot_idx

    for stop in stops:
        travel = time_matrix[current_pos][stop["idx"]]
        arrival = current_time + travel

        if arrival > stop["latest_min"]:
            return False, []

        # Driver waits if they arrive before the window opens
        current_time = max(arrival, stop["earliest_min"])
        arrival_times.append(arrival)
        current_pos = stop["idx"]

    return True, arrival_times
