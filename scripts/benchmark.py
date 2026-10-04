import subprocess
import sys
import time


def main() -> None:
    start = time.monotonic()
    run = subprocess.run([sys.executable, "-m", "phelmet.app", "--source", "data/sample/road.mp4", "--mock-imu", "--mock-gps", "--headless"], text=True, capture_output=True)
    print(run.stdout.strip())
    print(f"wall={time.monotonic()-start:.1f}s cpu%=measure on this computer")
    print("PASS/FAIL: compare p95 summary with 180 ms target")


if __name__ == "__main__":
    main()
