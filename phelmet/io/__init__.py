import csv
import time
from pathlib import Path

import cv2


class VideoSource:
    def __init__(self, path: str, pace: bool = True) -> None:
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise ValueError(f"cannot open video: {path}")
        self.delay = 1 / max(self.cap.get(cv2.CAP_PROP_FPS), 1)
        self.pace = pace
        self.last = time.monotonic()

    def read(self):
        if self.pace:
            left = self.delay - (time.monotonic() - self.last)
            if left > 0:
                time.sleep(left)
        ok, img = self.cap.read()
        self.last = time.monotonic()
        return ok, img

    def close(self) -> None:
        self.cap.release()


class CsvImu:
    def __init__(self, path: str) -> None:
        self.rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
        self.i = 0

    def read(self) -> dict:
        row = self.rows[min(self.i, len(self.rows) - 1)]
        self.i += 1
        return {k: float(v) for k, v in row.items()}


class MockImu:
    def __init__(self) -> None:
        self.t0 = time.monotonic()

    def read(self) -> dict:
        t = time.monotonic() - self.t0
        pitch = 8.0 if int(t) % 8 < 6 else 35.0
        return {"pitch": pitch, "gyro_y": 0.0, "t": t}


class CsvGps:
    def __init__(self, path: str) -> None:
        self.rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
        self.i = 0

    def read(self) -> dict:
        row = self.rows[min(self.i, len(self.rows) - 1)]
        self.i += 1
        return {k: float(v) for k, v in row.items()}


class MockGps:
    def __init__(self, speed_kmh: float = 40.0, lat: float = 12.9716, lon: float = 77.5946, hz: float = 20.0) -> None:
        self.speed_kmh, self.lat, self.lon = speed_kmh, lat, lon
        self.step = speed_kmh / 3.6 / hz / 111111

    def read(self) -> dict:
        row = {"speed_kmh": self.speed_kmh, "lat": self.lat, "lon": self.lon}
        self.lat += self.step
        self.lon += self.step * .25
        return row
