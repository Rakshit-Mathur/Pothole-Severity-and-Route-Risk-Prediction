import queue
import threading

import cv2

from ..pipeline.overlay import draw


class Viewer:
    def __init__(self, fps: float, show: bool = False, path: str | None = None) -> None:
        self.fps, self.show, self.path = fps, show, path
        self.q = queue.Queue(maxsize=1)
        self.stop = threading.Event()
        self.quit = False
        self.writer = None
        self.last = None
        self.last_num = 0
        self.alert_until = 0
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def put(self, frame, info: dict) -> None:
        if self.q.full():
            self.q.get_nowait()
        self.q.put_nowait((frame, info))

    def _open(self, img) -> None:
        if self.path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(self.path, fourcc, self.fps, (img.shape[1], img.shape[0]))

    def _show(self, img) -> None:
        if not self.show:
            return
        try:
            cv2.imshow("phelmet", img)
            if cv2.waitKey(1) & 255 == ord("q"):
                self.quit = True
        except cv2.error:
            print("debug view unavailable; continuing without a window")
            self.show = False

    def _write(self, img, num: int) -> None:
        if self.writer:
            for _ in range(max(0, num - self.last_num - 1)):
                self.writer.write(self.last)
            self.writer.write(img)
        self.last, self.last_num = img, num

    def _run(self) -> None:
        while not self.stop.is_set() or not self.q.empty():
            try:
                frame, info = self.q.get(timeout=.1)
            except queue.Empty:
                continue
            if info["alert"]:
                self.alert_until = info["num"] + int(self.fps * .5)
            info = info.copy()
            info["alert"] = info["num"] <= self.alert_until
            img = draw(frame, info)
            if self.writer is None:
                self._open(img)
            self._write(img, info["num"])
            self._show(img)

    def close(self) -> None:
        self.stop.set()
        self.thread.join(2)
        if self.writer:
            self.writer.release()
        if self.show:
            cv2.destroyAllWindows()
