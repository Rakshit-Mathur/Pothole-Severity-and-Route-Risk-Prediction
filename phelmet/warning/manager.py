import queue
import threading

from ..timing import now_ns


class Warning:
    def __init__(self, actuator, fired=None) -> None:
        self.actuator = actuator
        self.fired = fired
        self.q = queue.Queue()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def send(self, alert) -> None:
        self.q.put_nowait(alert)

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                alert = self.q.get(timeout=.1)
            except queue.Empty:
                continue
            self.actuator.beep(alert.severity)
            if self.fired:
                self.fired(alert, now_ns())

    def close(self) -> None:
        self.stop.set()
        self.thread.join(1)
        self.actuator.close()
