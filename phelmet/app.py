import argparse
import logging
import time

from .config import load_cfg
from .io import CsvGps, MockGps, MockImu, VideoSource
from .io.viewer import Viewer
from .pose import PoseLoop
from .runner import run_loop
from .storage.road_store import export_geojson


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--source")
    ap.add_argument("--mock-imu", action="store_true")
    ap.add_argument("--mock-gps", action="store_true")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--debug-view", action="store_true")
    ap.add_argument("--save-video")
    ap.add_argument("--db")
    ap.add_argument("--export-geojson")
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    logging.basicConfig(level=logging.INFO)
    path = args.source or cfg["camera"]["source"]
    if path in ("0", "picam"):
        raise ValueError("this software demonstration accepts a video file")
    source = VideoSource(path)
    imu = PoseLoop(MockImu(), cfg["imu"]["rate_hz"])
    gps = MockGps(cfg["gps"]["fallback_kmh"], cfg["gps"]["mock_lat"], cfg["gps"]["mock_lon"], 1 / source.delay) if args.mock_gps else CsvGps("data/sample/gps.csv")
    started = time.monotonic()
    viewer = Viewer(1 / source.delay, args.debug_view, args.save_video) if args.debug_view or args.save_video else None
    if viewer:
        viewer.start()
    try:
        db_path = args.db or cfg["storage"]["db_path"]
        result = run_loop(source, imu, cfg, gps, viewer=viewer, db_path=db_path)
        if args.export_geojson:
            export_geojson(db_path, args.export_geojson)
    except KeyboardInterrupt:
        print("stopping")
        result = {"frames": 0, "p50_ms": 0, "p95_ms": 0}
    elapsed = time.monotonic() - started
    print(f"summary {elapsed:.1f}s frames={result['frames']} p50={result['p50_ms']:.1f}ms p95={result['p95_ms']:.1f}ms")


if __name__ == "__main__":
    main()
