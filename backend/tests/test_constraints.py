from datetime import time

from app.services.constraint_checker import (
    check_capacity,
    check_time_window,
    time_to_minutes,
    validate_route,
)


def test_time_to_minutes_basic():
    assert time_to_minutes(time(8, 0)) == 480.0
    assert time_to_minutes(time(12, 30)) == 750.0
    assert time_to_minutes(time(0, 0)) == 0.0
    assert time_to_minutes(time(23, 59, 59)) > 1439.0


def test_check_time_window_on_boundary():
    assert check_time_window(480.0, time(8, 0), time(12, 0)) is True
    assert check_time_window(720.0, time(8, 0), time(12, 0)) is True


def test_check_time_window_inside():
    assert check_time_window(600.0, time(8, 0), time(12, 0)) is True


def test_check_time_window_too_late():
    assert check_time_window(721.0, time(8, 0), time(12, 0)) is False


def test_check_time_window_too_early():
    assert check_time_window(479.9, time(8, 0), time(12, 0)) is False


def test_capacity_valid():
    assert check_capacity([10.0, 20.0, 30.0], 100.0) is True


def test_capacity_exact():
    assert check_capacity([50.0, 50.0], 100.0) is True


def test_capacity_exceeded():
    assert check_capacity([60.0, 50.0], 100.0) is False


def test_validate_route_valid():
    dist = [[0, 1, 2], [1, 0, 1], [2, 1, 0]]
    stops = [
        {"idx": 1, "weight": 10, "earliest_min": 482, "latest_min": 720},
        {"idx": 2, "weight": 10, "earliest_min": 485, "latest_min": 720},
    ]
    valid, arrivals = validate_route(stops, 100.0, dist, dist, depot_idx=0, start_time_min=480.0)
    assert valid is True
    assert len(arrivals) == 2


def test_validate_route_over_capacity():
    dist = [[0, 1], [1, 0]]
    stops = [{"idx": 1, "weight": 200, "earliest_min": 480, "latest_min": 720}]
    valid, _ = validate_route(stops, 100.0, dist, dist, depot_idx=0)
    assert valid is False


def test_validate_route_missed_time_window():
    # travel time = 500 minutes, window closes at 481 — impossible
    time_m = [[0, 500], [500, 0]]
    dist = [[0, 1], [1, 0]]
    stops = [{"idx": 1, "weight": 5, "earliest_min": 480, "latest_min": 481}]
    valid, _ = validate_route(stops, 100.0, dist, time_m, depot_idx=0, start_time_min=480.0)
    assert valid is False
