from phelmet.decision import Decision
from phelmet.tracker import Track
from phelmet.types import Detection


def test_confirmed_track_is_logged_once():
    cfg = {"camera": {"height": 240, "height_m": 1.5, "focal_px": 300, "pitch_deg": 8}}
    near = Track(1, Detection((10, 180, 50, 10), .9, .8), [True, True])
    far = Track(2, Detection((10, 140, 50, 10), .9, .8), [True, True])
    out = Decision(cfg).assess([far, near], True)
    assert len(out) == 2 and near.logged
    assert not Decision(cfg).assess([near], True)


def test_head_away_has_no_log_rows():
    cfg = {"camera": {"height": 240, "height_m": 1.5, "focal_px": 300, "pitch_deg": 8}}
    assert Decision(cfg).assess([], False) == []
