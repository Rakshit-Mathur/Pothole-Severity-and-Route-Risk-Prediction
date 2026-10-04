import numpy as np

from phelmet.roi import get_roi, pose_ok
from phelmet.types import Pose


def test_head_away_is_gated():
    cfg = {"imu": {"pitch_min": -5, "pitch_max": 25, "max_rate_dps": 55}, "camera": {"focal_px": 300}, "roi": {"fixed_top": 90}}
    img = np.zeros((240, 320, 3), np.uint8)
    pose = Pose(35, 0, 0, True)
    assert not pose_ok(pose, cfg)
    assert get_roi(img, pose, cfg) is None
