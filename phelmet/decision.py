from .geometry import get_distance, get_tti, get_width_cm
from .types import Alert


class Decision:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.state = "NORMAL"
        self.last_burst = -99.0

    def set_state(self, name: str) -> None:
        if name != self.state:
            print(f"state {self.state} -> {name}")
            self.state = name

    def choose(self, tracks, speed_mps: float, pose_good: bool, now: float, t_ns: int, wall_ts: str = ""):
        if not pose_good:
            self.set_state("ROAD_NOT_VISIBLE")
            return None
        self.set_state("NORMAL")
        cam, dc = self.cfg["camera"], self.cfg["decision"]
        scale = max(0.6, speed_mps / (self.cfg["gps"]["fallback_kmh"] / 3.6))
        items = []
        for trk in tracks:
            x, y, w, h = trk.det.box
            dist = get_distance(y+h, cam["height"] / 2, cam["focal_px"], cam["height_m"], cam["pitch_deg"])
            if dist is not None:
                items.append((dist, trk, get_tti(dist, speed_mps)))
        for dist, trk, tti in sorted(items, key=lambda item: item[0]):
            if trk.alerted:
                continue
            if tti and dc["tti_min_s"] * scale <= tti <= dc["tti_max_s"] * scale:
                trk.last_alert = now
                trk.alerted = True
                trk.alert_ts = wall_ts
                width = get_width_cm(trk.det.box[2], dist, cam["focal_px"])
                severity = self.severity(width, trk.det.conf, trk.det.dark)
                if now - self.last_burst < dc["rough_patch_s"]:
                    severity = "ROUGH_PATCH"
                self.last_burst = now
                return Alert(t_ns, dist, tti, severity, trk.id, trk.max_conf, wall_ts)
        return None

    def severity(self, width: float, conf: float, dark: float) -> str:
        score = width * conf * (0.7 + dark)
        if score > 70:
            return "HIGH"
        if score > 35:
            return "MEDIUM"
        return "LOW"
