import pytest

from app.services.distance_matrix import haversine_matrix


def test_zero_diagonal():
    coords = [(47.6062, -122.3321), (47.6200, -122.3500)]
    dist, time_m = haversine_matrix(coords)
    assert dist[0][0] == pytest.approx(0, abs=1e-9)
    assert dist[1][1] == pytest.approx(0, abs=1e-9)


def test_symmetric():
    coords = [(47.6062, -122.3321), (47.6200, -122.3500), (47.5900, -122.3000)]
    dist, _ = haversine_matrix(coords)
    for i in range(len(coords)):
        for j in range(len(coords)):
            assert dist[i][j] == pytest.approx(dist[j][i], abs=1e-9)


def test_known_distance_seattle():
    # Seattle city center to ~2 km north — should be 1.8–2.2 km
    coords = [(47.6062, -122.3321), (47.6242, -122.3321)]
    dist, _ = haversine_matrix(coords)
    assert 1.8 < dist[0][1] < 2.2


def test_time_matrix_proportional_to_distance():
    coords = [(47.6062, -122.3321), (47.6242, -122.3321)]
    dist, time_m = haversine_matrix(coords, avg_speed_kmh=30.0)
    expected_time = dist[0][1] / 30.0 * 60
    assert time_m[0][1] == pytest.approx(expected_time, rel=1e-6)


def test_three_node_triangle_inequality():
    coords = [(47.60, -122.33), (47.62, -122.35), (47.61, -122.30)]
    dist, _ = haversine_matrix(coords)
    # d(A,C) <= d(A,B) + d(B,C)
    assert dist[0][2] <= dist[0][1] + dist[1][2] + 1e-9
