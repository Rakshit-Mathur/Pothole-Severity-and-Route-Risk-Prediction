import time
from datetime import datetime

from .capture import Capture
from .decision import Decision
from .detector import MockDetector, OnnxDetector
from .io import MockGps
from .geometry import get_distance
from .roi import check_blur, check_road, get_horizon, get_roi, pose_ok
from .scheduler import Scheduler
from .timing import Rolling, Timer, now_ns
from .tracker import Tracker
from .storage import RoadStore


def make_detector(cfg: dict):
    c = cfg["detector"]
    return MockDetector(c["confidence"]) if c["kind"] == "mock" else OnnxDetector(c["model"], c["input_size"], c["confidence"], c.get("nms_iou", .45), c.get("max_box_area", .18))


def view_info(frame, tracks, cfg, decide, speed, pose, latency, fps):
    cam = cfg["camera"]
    top = get_horizon(frame.img.shape[0] / 2, cam["focal_px"], pose.pitch_deg) if pose.ok else cfg["roi"]["fixed_top"]
    top = max(0, min(frame.img.shape[0] - 2, top))
    items = []
    for trk in tracks:
        x, y, w, h = trk.det.box
        dist = get_distance(y+h, cam["height"] / 2, cam["focal_px"], cam["height_m"], cam["pitch_deg"])
        width = w * dist / cam["focal_px"] * 100 if dist else 0
        sev = decide.severity(width, trk.det.conf, trk.det.dark)
        items.append({"box": trk.det.box, "id": trk.id, "conf": trk.det.conf, "confirmed": sum(trk.seen) >= cfg["tracker"]["confirm_n"], "dist": dist or 0, "severity": sev})
    h, w = frame.img.shape[:2]
    return {"tracks": items, "roi": [(0, top), (w-1, top), (w-1, h-1), (0, h-1)], "horizon": top, "state": decide.state, "speed": speed * 3.6, "pitch": pose.pitch_deg, "fps": fps, "latency": latency, "num": frame.num}


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def run_loop(source, imu_loop, cfg: dict, gps=None, limit: int = 0, viewer=None, db_path=None) -> dict:
    gps = gps or MockGps(cfg["gps"]["fallback_kmh"], cfg["gps"]["mock_lat"], cfg["gps"]["mock_lon"], 1 / source.delay)
    cap, det, trk = Capture(source), make_detector(cfg), Tracker(cfg["tracker"])
    decide = Decision(cfg)
    lat, infer = Rolling(), Rolling()
    sch = Scheduler(cfg["decision"]["latency_p95_ms"])
    store = RoadStore(db_path or cfg["storage"]["db_path"], cfg["storage"]["dedup_radius_m"])
    store.start()
    cap.start(); imu_loop.start()
    count = 0
    try:
        while not cap.stop.is_set() and (not limit or count < limit):
            frame = cap.get()
            if frame is None:
                continue
            count += 1
            pose = imu_loop.get(frame.t_capture_ns)
            gps_row = gps.read()
            store.point(gps_row, stamp())
            speed = gps_row["speed_kmh"] / 3.6
            tracks = trk.tracks
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
                    wall_ts = stamp()
                    tracks = trk.update(dets, time.monotonic(), wall_ts)
                    for found, dist, severity in decide.assess(tracks, pose_ok(pose, cfg)):
                        if not gps_row.get("fix_ok") or gps_row.get("hdop", 99) > cfg["gps"].get("max_hdop", 4.0):
                            continue
                        store.pothole((wall_ts, gps_row["lat"], gps_row["lon"], found.max_conf, severity, dist))
                        print(f"[{wall_ts}] logged pothole id {found.id}, conf {found.max_conf:.2f}, {severity}")
            latency = (now_ns() - frame.t_capture_ns) / 1e6
            lat.add(latency)
            sch.update(lat.p95())
            if viewer:
                viewer.put(frame.img, view_info(frame, tracks, cfg, decide, speed, pose, latency, 1 / source.delay))
            if viewer and viewer.quit:
                break
    finally:
        cap.close(); imu_loop.close(); store.close()
        if viewer:
            viewer.close()
    return {"frames": count, "drops": cap.drops, "p50_ms": lat.p50(), "p95_ms": lat.p95(), "infer_p95_ms": infer.p95()}
