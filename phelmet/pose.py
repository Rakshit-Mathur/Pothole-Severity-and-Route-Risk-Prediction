import threading
import time

from .timing import now_ns
from .types import Pose


class PoseLoop:
    def __init__(self, imu, rate_hz: int = 100) -> None:
        self.imu = imu
        self.delay = 1 / rate_hz
        self.pose = Pose(0, 0, now_ns(), False)
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _run(self) -> None:
        last = time.monotonic()
        pitch = 0.0
        while not self.stop.is_set():
            row = self.imu.read()
            dt = time.monotonic() - last
            last = time.monotonic()
            gyro = row.get("gyro_y", 0.0)
            measured = row.get("pitch", pitch)
            pitch = 0.98 * (pitch + gyro * dt) + 0.02 * measured
            with self.lock:
                self.pose = Pose(pitch, abs(gyro), now_ns(), True)
            time.sleep(self.delay)

    def get(self, t_ns: int) -> Pose:
        with self.lock:
            return self.pose

    def close(self) -> None:
        self.stop.set()
        self.thread.join(1)
