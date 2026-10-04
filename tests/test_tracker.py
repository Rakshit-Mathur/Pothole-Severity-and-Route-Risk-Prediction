from phelmet.tracker import Tracker
from phelmet.types import Detection


def test_confirm_two_of_three():
    tr = Tracker({"iou_min": .2, "confirm_n": 2, "confirm_m": 3, "cooldown_s": 2})
    det = Detection((10, 10, 20, 8), .9)
    assert not tr.update([det], 0)
    found = tr.update([det], .1)
    assert len(found) == 1
    found[0].last_alert = .1
    assert not tr.update([det], .2)
