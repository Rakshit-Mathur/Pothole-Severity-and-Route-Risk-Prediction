import time

import cv2
import numpy as np

from phelmet.io import MockGps
from phelmet.pose import PoseLoop
from phelmet.runner import run_loop


class SmallSource:
    def __init__(self):
        self.i = 0

    def read(self):
        time.sleep(.02)
        self.i += 1
        if self.i > 45:
            return False, None
        img = np.full((240, 320, 3), (78, 88, 82), np.uint8)
        if self.i > 5:
            cv2.ellipse(img, (160, 165), (22, 7), 0, 0, 360, (15, 15, 15), -1)
        return True, img

    def close(self):
        pass


class StraightImu:
    def read(self):
        return {"pitch": 8, "gyro_y": 0}


def test_replay_logs_pothole(tmp_path):
    cfg = {"camera": {"height": 240, "height_m": 1.55, "focal_px": 300, "pitch_deg": 8}, "imu": {"pitch_min": -5, "pitch_max": 25, "max_rate_dps": 55, "rate_hz": 100}, "roi": {"fixed_top": 90, "blur_min": 1, "sat_min": 2, "texture_min": 1, "edge_min": .001}, "detector": {"kind": "mock", "confidence": .4, "input_size": 320}, "tracker": {"iou_min": .2, "confirm_n": 2, "confirm_m": 3, "cooldown_s": 3, "lost_frames": 3}, "gps": {"fallback_kmh": 40, "mock_lat": 12.9, "mock_lon": 77.5}, "decision": {"latency_p95_ms": 180}, "storage": {"db_path": "unused.db", "dedup_radius_m": 8}}
    db = str(tmp_path / "road.db")
    result = run_loop(SmallSource(), PoseLoop(StraightImu()), cfg, MockGps(), db_path=db)
    assert result["frames"]
