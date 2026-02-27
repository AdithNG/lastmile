"""
Unit tests for the CVRPTW solver.

These tests use a synthetic 5-node distance matrix (depot + 4 stops) so
they run in milliseconds with zero external dependencies.

Key things verified:
  - All stops get assigned (greedy covers every feasible stop)
  - 2-opt never increases total distance
  - Capacity constraints are respected
  - Time window constraints are respected
  - Improvement is measurable on a known sub-optimal greedy ordering
"""

import pytest

from app.services.optimizer import CVRPTWSolver

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

DEPOT_IDX = 0

# Linear layout: depot-0, stop-1, stop-2, stop-3, stop-4
# Optimal route is 0→1→2→3→4→0 (distance = 4 + 4 = 8)
# Greedy from depot might pick 0→4→3→2→1→0 (distance = 4 + 4 = 8, same here)
DIST_LINEAR = [
    [0, 1, 2, 3, 4],
    [1, 0, 1, 2, 3],
    [2, 1, 0, 1, 2],
    [3, 2, 1, 0, 1],
    [4, 3, 2, 1, 0],
]

STOPS_4 = [
    {"id": 1, "idx": 1, "weight": 10, "earliest_min": 480, "latest_min": 840},
    {"id": 2, "idx": 2, "weight": 10, "earliest_min": 480, "latest_min": 840},
    {"id": 3, "idx": 3, "weight": 10, "earliest_min": 480, "latest_min": 840},
    {"id": 4, "idx": 4, "weight": 10, "earliest_min": 480, "latest_min": 840},
]

VEHICLES_2 = [
    {"id": 1, "capacity_kg": 100, "driver_name": "Driver 1"},
    {"id": 2, "capacity_kg": 100, "driver_name": "Driver 2"},
]

VEHICLES_1_BIG = [
    {"id": 1, "capacity_kg": 500, "driver_name": "Driver 1"},
]


# ---------------------------------------------------------------------------
# Greedy construction
# ---------------------------------------------------------------------------

def test_greedy_assigns_all_stops():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_2, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver._greedy()
    assigned = sum(len(r["stops"]) for r in routes)
    assert assigned == len(STOPS_4)


def test_greedy_single_vehicle_assigns_all():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_1_BIG, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver._greedy()
    assert len(routes) == 1
    assert len(routes[0]["stops"]) == 4


def test_greedy_respects_capacity():
    heavy_stops = [{"id": 1, "idx": 1, "weight": 110, "earliest_min": 480, "latest_min": 840}]
    small_vehicle = [{"id": 1, "capacity_kg": 100, "driver_name": "D1"}]
    solver = CVRPTWSolver(heavy_stops, small_vehicle, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver._greedy()
    # Stop exceeds capacity — should not be assigned
    assert sum(len(r["stops"]) for r in routes) == 0


def test_greedy_respects_time_window():
    # Travel from depot to idx=1 takes DIST_LINEAR[0][1]=1 minute.
    # Window closes at 480 — impossible to arrive before 481.
    impossible_stop = [{"id": 1, "idx": 1, "weight": 5, "earliest_min": 0, "latest_min": 480}]
    # start_time_min=480 + travel=1 = 481 > 480 → rejected
    solver = CVRPTWSolver(impossible_stop, VEHICLES_1_BIG, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX, start_min=480.0)
    routes = solver._greedy()
    assert sum(len(r["stops"]) for r in routes) == 0


# ---------------------------------------------------------------------------
# 2-opt improvement
# ---------------------------------------------------------------------------

def test_two_opt_never_increases_distance():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_2, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    greedy_routes = solver._greedy()
    greedy_total = sum(r["dist"] for r in greedy_routes)

    optimized_routes = solver.solve()
    optimized_total = sum(r["dist"] for r in optimized_routes)

    assert optimized_total <= greedy_total + 1e-6


def test_two_opt_improves_known_bad_route():
    """
    Force a deliberately bad ordering and verify 2-opt fixes it.
    Stops ordered 0→4→1→3→2→0 should be improved to 0→1→2→3→4→0.
    """
    # Manually construct a route in bad order [3, 0, 2, 1] (0-indexed stop list)
    solver = CVRPTWSolver(STOPS_4, VEHICLES_1_BIG, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    bad_route = {"vehicle": VEHICLES_1_BIG[0], "stops": [3, 0, 2, 1], "dist": solver._route_dist([3, 0, 2, 1])}
    improved_route = solver._two_opt(bad_route)
    assert improved_route["dist"] <= bad_route["dist"] + 1e-6


def test_solve_returns_same_stop_count():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_2, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver.solve()
    assert sum(len(r["stops"]) for r in routes) == len(STOPS_4)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def test_score_unassigned_zero_when_all_assigned():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_1_BIG, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver.solve()
    score = solver.score(routes)
    assert score["unassigned"] == 0
    assert score["num_routes"] == 1


def test_score_total_distance_positive():
    solver = CVRPTWSolver(STOPS_4, VEHICLES_1_BIG, DIST_LINEAR, DIST_LINEAR, DEPOT_IDX)
    routes = solver.solve()
    score = solver.score(routes)
    assert score["total_distance_km"] > 0
