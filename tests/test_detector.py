import numpy as np

from phelmet.detector import OnnxDetector


def test_letterbox_keeps_wide_frame_shape():
    det = object.__new__(OnnxDetector)
    det.size = 320
    x, scale, left, top = det.prep(np.zeros((360, 640, 3), np.uint8))
    assert x.shape == (1, 3, 320, 320)
    assert scale == .5 and left == 0 and top == 70


def test_area_filter_blocks_merged_road_box():
    det = object.__new__(OnnxDetector)
    det.size, det.conf, det.nms_iou, det.max_area = 320, .4, .45, .18
    raw = np.zeros((1, 5, 6), np.float32)
    raw[0, :, 0] = [160, 160, 320, 320, .9]
    det.session = type("Session", (), {"get_inputs": lambda s: [type("In", (), {"name": "images"})()], "run": lambda s, a, b: [raw]})()
    assert det.detect(np.zeros((360, 640, 3), np.uint8)) == []
