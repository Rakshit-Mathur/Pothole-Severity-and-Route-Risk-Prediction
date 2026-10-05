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
    def __init__(self, speed_kmh: float = 40.0) -> None:
        self.speed_kmh = speed_kmh

    def read(self) -> dict:
        return {"speed_kmh": self.speed_kmh, "lat": 0.0, "lon": 0.0}


class ConsoleActuator:
    def beep(self, severity: str) -> None:
        pass

    def close(self) -> None:
        pass
