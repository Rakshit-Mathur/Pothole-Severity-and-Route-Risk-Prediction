from phelmet.geometry import get_distance, get_tti, get_width_cm


def test_ground_geometry():
    dist = get_distance(180, 120, 300, 1.5, 8)
    assert dist is not None
    assert 3 < dist < 5
    assert 60 < get_width_cm(50, dist, 300) < 80
    assert 0.3 < get_tti(dist, 11.1) < 0.5


def test_horizon_has_no_distance():
    assert get_distance(80, 120, 300, 1.5, 0) is None
