from phelmet.decision import Decision
from phelmet.tracker import Track
from phelmet.types import Detection


def test_nearest_alert_wins():
    cfg = {"camera": {"height": 240, "height_m": 1.5, "focal_px": 300, "pitch_deg": 8}, "gps": {"fallback_kmh": 40}, "decision": {"tti_min_s": .1, "tti_max_s": 5, "rough_patch_s": 1.5}}
    near = Track(1, Detection((10, 180, 50, 10), .9, .8), [True, True])
    far = Track(2, Detection((10, 140, 50, 10), .9, .8), [True, True])
    out = Decision(cfg).choose([far, near], 11.1, True, 1, 0)
    assert out and out.track_id == 1


def test_head_away_no_alert():
    cfg = {"camera": {"height": 240, "height_m": 1.5, "focal_px": 300, "pitch_deg": 8}, "gps": {"fallback_kmh": 40}, "decision": {"tti_min_s": .1, "tti_max_s": 5, "rough_patch_s": 1.5}}
    assert Decision(cfg).choose([], 11.1, False, 1, 0) is None
