import numpy as np

from phelmet.pipeline.overlay import draw, to_full


def info(state="NORMAL"):
    return {"tracks": [{"box": (20, 80, 40, 16), "id": 3, "conf": .82, "confirmed": True, "dist": 7.4, "severity": "MEDIUM"}], "roi": [(0, 60), (159, 60), (159, 119), (0, 119)], "horizon": 60, "state": state, "speed": 40, "pitch": 8, "fps": 20, "latency": 8, "num": 1}


def test_draw_copy_and_box():
    img = np.full((120, 160, 3), 30, np.uint8)
    out = draw(img, info())
    assert out.shape == img.shape
    assert np.array_equal(img, np.full((120, 160, 3), 30, np.uint8))
    assert not np.array_equal(out[80, 20], img[80, 20])


def test_crop_offset_and_hidden_boxes():
    assert to_full((10, 20, 30, 40), 50, .5) == (20, 90, 60, 80)
    out = draw(np.full((120, 160, 3), 30, np.uint8), info("ROAD_NOT_VISIBLE"))
    assert out[80, 20].max() < 200
