import argparse
import logging
import time

from .config import load_cfg
from .io import ConsoleActuator, CsvGps, MockGps, MockImu, VideoSource
from .pose import PoseLoop
from .runner import run_loop


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--source")
    ap.add_argument("--mock-imu", action="store_true")
    ap.add_argument("--mock-gps", action="store_true")
    ap.add_argument("--no-dashboard", action="store_true")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--debug-view", action="store_true")
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    logging.basicConfig(level=logging.INFO)
    path = args.source or cfg["camera"]["source"]
    if path in ("0", "picam"):
        raise ValueError("live camera support is added in M8; use a video file for replay")
    source = VideoSource(path)
    imu = PoseLoop(MockImu(), cfg["imu"]["rate_hz"])
    gps = MockGps(cfg["gps"]["fallback_kmh"]) if args.mock_gps else CsvGps("data/sample/gps.csv")
    started = time.monotonic()
    try:
        result = run_loop(source, imu, ConsoleActuator(), cfg, gps)
    except KeyboardInterrupt:
        print("stopping")
        result = {"frames": 0, "p50_ms": 0, "p95_ms": 0, "alerts": []}
    elapsed = time.monotonic() - started
    print(f"summary {elapsed:.1f}s frames={result['frames']} p50={result['p50_ms']:.1f}ms p95={result['p95_ms']:.1f}ms alerts={len(result['alerts'])}")


if __name__ == "__main__":
    main()
