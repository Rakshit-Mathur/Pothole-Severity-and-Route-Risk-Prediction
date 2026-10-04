import csv
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    out = Path("data/sample")
    out.mkdir(parents=True, exist_ok=True)
    w, h, fps, frames = 320, 240, 20, 300
    video = cv2.VideoWriter(str(out / "road.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i in range(frames):
        img = np.full((h, w, 3), (78, 88, 82), np.uint8)
        for y in range(75, h, 12):
            cv2.line(img, (0, y + i % 12), (w, y + i % 12), (76, 79, 75), 1)
        for start in (50, 155, 250):
            age = i - start
            if 0 < age < 70:
                y = 102 + age * 0.7
                r = 4 + age // 10
                cv2.ellipse(img, (160, int(min(y, 228))), (r, max(2, r // 3)), 0, 0, 360, (18, 18, 18), -1)
        video.write(img)
    video.release()
    with (out / "imu.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["t", "pitch", "gyro_y"])
        wr.writeheader()
        for i in range(frames * 5):
            t = i / 100
            away = 3.5 < t < 5 or 10 < t < 11
            wr.writerow({"t": t, "pitch": 34 if away else 8, "gyro_y": 80 if away else 0})
    with (out / "gps.csv").open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["speed_kmh", "lat", "lon"])
        wr.writeheader()
        for _ in range(frames):
            wr.writerow({"speed_kmh": 40, "lat": 12.97, "lon": 77.59})


if __name__ == "__main__":
    main()
