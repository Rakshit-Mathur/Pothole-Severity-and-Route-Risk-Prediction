import time

from .capture import Capture
from .decision import Decision
from .detector import MockDetector, OnnxDetector
from .io import MockGps
from .roi import check_blur, check_road, get_roi, pose_ok
from .scheduler import Scheduler
from .timing import Rolling, Timer, now_ns
from .tracker import Tracker


def make_detector(cfg: dict):
    c = cfg["detector"]
    return MockDetector(c["confidence"]) if c["kind"] == "mock" else OnnxDetector(c["model"], c["input_size"], c["confidence"])


def run_loop(source, imu_loop, actuator, cfg: dict, gps=None, limit: int = 0) -> dict:
    gps = gps or MockGps(cfg["gps"]["fallback_kmh"])
    cap, det, trk = Capture(source), make_detector(cfg), Tracker(cfg["tracker"])
    decide = Decision(cfg)
    lat, infer = Rolling(), Rolling()
    fired = []
    from .warning import Warning
    warn = Warning(actuator, lambda a, t: fired.append((a, (t-a.t_ns)/1e6)))
    sch = Scheduler(cfg["decision"]["latency_p95_ms"])
    cap.start(); imu_loop.start(); warn.start()
    count = 0
    try:
        while not cap.stop.is_set() and (not limit or count < limit):
            frame = cap.get()
            if frame is None:
                continue
            count += 1
            pose = imu_loop.get(frame.t_capture_ns)
            crop = get_roi(frame.img, pose, cfg)
            if crop is None:
                decide.set_state("ROAD_NOT_VISIBLE")
                continue
            roi, top = crop
            if not check_road(roi, cfg) or not check_blur(roi, cfg):
                decide.set_state("DEGRADED")
                continue
            if not sch.should_run():
                continue
            timer = Timer()
            dets = det.detect(roi)
            infer.add(timer.ms())
            for d in dets:
                x, y, w, h = d.box
                d.box = (x, y + top, w, h)
            tracks = trk.update(dets, time.monotonic())
            speed = gps.read().get("speed_kmh", cfg["gps"]["fallback_kmh"]) / 3.6
            alert = decide.choose(tracks, speed, pose_ok(pose, cfg), time.monotonic(), frame.t_capture_ns)
            if alert:
                warn.send(alert)
            lat.add((now_ns() - frame.t_capture_ns) / 1e6)
            sch.update(lat.p95())
    finally:
        cap.close(); imu_loop.close(); warn.close()
    return {"frames": count, "drops": cap.drops, "p50_ms": lat.p50(), "p95_ms": lat.p95(), "infer_p95_ms": infer.p95(), "alerts": fired}
