import time

from .capture import Capture
from .decision import Decision
from .detector import MockDetector, OnnxDetector
from .io import MockGps
from .geometry import get_distance, get_tti
from .roi import check_blur, check_road, get_horizon, get_roi, pose_ok
from .scheduler import Scheduler
from .timing import Rolling, Timer, now_ns
from .tracker import Tracker


def make_detector(cfg: dict):
    c = cfg["detector"]
    return MockDetector(c["confidence"]) if c["kind"] == "mock" else OnnxDetector(c["model"], c["input_size"], c["confidence"])


def view_info(frame, tracks, cfg, decide, speed, pose, latency, alert, fps):
    cam = cfg["camera"]
    top = get_horizon(frame.img.shape[0] / 2, cam["focal_px"], pose.pitch_deg) if pose.ok else cfg["roi"]["fixed_top"]
    top = max(0, min(frame.img.shape[0] - 2, top))
    items = []
    for trk in tracks:
        x, y, w, h = trk.det.box
        dist = get_distance(y+h, cam["height"] / 2, cam["focal_px"], cam["height_m"], cam["pitch_deg"])
        tti = get_tti(dist, speed) if dist else None
        width = w * dist / cam["focal_px"] * 100 if dist else 0
        sev = decide.severity(width, trk.det.conf, trk.det.dark)
        if alert and alert.track_id == trk.id:
            sev = alert.severity
        items.append({"box": trk.det.box, "id": trk.id, "conf": trk.det.conf, "confirmed": sum(trk.seen) >= cfg["tracker"]["confirm_n"], "dist": dist or 0, "tti": tti or 0, "severity": sev})
    h, w = frame.img.shape[:2]
    return {"tracks": items, "roi": [(0, top), (w-1, top), (w-1, h-1), (0, h-1)], "horizon": top, "state": decide.state, "speed": speed * 3.6, "pitch": pose.pitch_deg, "fps": fps, "latency": latency, "alert": bool(alert), "num": frame.num}


def run_loop(source, imu_loop, actuator, cfg: dict, gps=None, limit: int = 0, viewer=None) -> dict:
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
            speed = cfg["gps"]["fallback_kmh"] / 3.6
            tracks, alert = trk.tracks, None
            crop = get_roi(frame.img, pose, cfg)
            if crop is None:
                decide.set_state("ROAD_NOT_VISIBLE")
            else:
                roi, top = crop
                if not check_road(roi, cfg) or not check_blur(roi, cfg):
                    decide.set_state("DEGRADED")
                elif sch.should_run():
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
            latency = (now_ns() - frame.t_capture_ns) / 1e6
            lat.add(latency)
            sch.update(lat.p95())
            if viewer:
                viewer.put(frame.img, view_info(frame, tracks, cfg, decide, speed, pose, latency, alert, 1 / source.delay))
            if viewer and viewer.quit:
                break
    finally:
        cap.close(); imu_loop.close(); warn.close()
        if viewer:
            viewer.close()
    return {"frames": count, "drops": cap.drops, "p50_ms": lat.p50(), "p95_ms": lat.p95(), "infer_p95_ms": infer.p95(), "alerts": fired}
