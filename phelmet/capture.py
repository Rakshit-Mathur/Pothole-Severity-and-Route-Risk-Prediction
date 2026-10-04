import queue
import threading

from .timing import now_ns
from .types import Frame


class Capture:
    def __init__(self, source) -> None:
        self.source = source
        self.q = queue.Queue(maxsize=1)
        self.stop = threading.Event()
        self.drops = 0
        self.num = 0
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def _run(self) -> None:
        while not self.stop.is_set():
            ok, img = self.source.read()
            if not ok:
                self.stop.set()
                break
            self.num += 1
            frame = Frame(img, now_ns(), self.num)
            if self.q.full():
                self.q.get_nowait()
                self.drops += 1
            self.q.put_nowait(frame)

    def get(self, timeout: float = 0.2):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        self.stop.set()
        self.thread.join(1)
        self.source.close()
