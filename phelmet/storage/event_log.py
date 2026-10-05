import csv
import queue
import threading
from pathlib import Path


class EventLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.q = queue.Queue()
        self.open = {}
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def log_event(self, row: tuple) -> None:
        self.q.put(("event", row))

    def done(self, trk) -> None:
        self.q.put(("done", (trk.id, trk.max_conf)))

    def flush_open(self, tracks) -> None:
        for trk in tracks:
            self.done(trk)
        self.stop.set()
        self.thread.join(2)

    def _write(self, row: tuple) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            if new:
                wr.writerow(["first_seen", "alert_time", "track_id", "max_conf", "severity", "dist_m_at_alert"])
            wr.writerow(row)

    def _run(self) -> None:
        while not self.stop.is_set() or not self.q.empty():
            try:
                kind, row = self.q.get(timeout=.1)
            except queue.Empty:
                continue
            if kind == "event":
                self.open[row[2]] = row
            elif row[0] in self.open:
                event = list(self.open.pop(row[0]))
                event[3] = max(event[3], row[1])
                self._write(event)
                print(f"pothole id {row[0]} done, max conf {event[3]:.2f}")
