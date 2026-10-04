from dataclasses import dataclass, field

from .types import Detection


def iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, x2-x1) * max(0, y2-y1)
    return inter / (aw*ah + bw*bh - inter + 1e-6)


def near(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ((ax+aw/2-bx-bw/2) ** 2 + (ay+ah/2-by-bh/2) ** 2) ** .5 < 35


@dataclass
class Track:
    id: int
    det: Detection
    seen: list[bool] = field(default_factory=list)
    last_alert: float = -999.0


class Tracker:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.tracks = []
        self.next_id = 1

    def update(self, dets: list[Detection], now: float) -> list[Track]:
        used = set()
        for trk in self.tracks:
            best = max(range(len(dets)), key=lambda i: iou(trk.det.box, dets[i].box), default=-1)
            hit = best >= 0 and best not in used and (iou(trk.det.box, dets[best].box) >= self.cfg["iou_min"] or near(trk.det.box, dets[best].box))
            trk.seen.append(hit)
            trk.seen = trk.seen[-self.cfg["confirm_m"]:]
            if hit:
                trk.det = dets[best]
                used.add(best)
        for i, det in enumerate(dets):
            if i not in used:
                self.tracks.append(Track(self.next_id, det, [True]))
                self.next_id += 1
        self.tracks = [t for t in self.tracks if len(t.seen) < self.cfg["confirm_m"] or any(t.seen)]
        return [t for t in self.tracks if sum(t.seen) >= self.cfg["confirm_n"] and now - t.last_alert >= self.cfg["cooldown_s"]]
