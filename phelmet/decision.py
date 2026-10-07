from .geometry import get_distance, get_width_cm


class Decision:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.state = "NORMAL"

    def set_state(self, name: str) -> None:
        if name != self.state:
            print(f"state {self.state} -> {name}")
            self.state = name

    def assess(self, tracks, pose_good: bool):
        if not pose_good:
            self.set_state("ROAD_NOT_VISIBLE")
            return []
        self.set_state("NORMAL")
        cam = self.cfg["camera"]
        rows = []
        for trk in tracks:
            if trk.logged:
                continue
            x, y, w, h = trk.det.box
            dist = get_distance(y+h, cam["height"] / 2, cam["focal_px"], cam["height_m"], cam["pitch_deg"])
            if dist is not None:
                width = get_width_cm(trk.det.box[2], dist, cam["focal_px"])
                severity = self.severity(width, trk.det.conf, trk.det.dark)
                trk.logged = True
                rows.append((trk, dist, severity))
        return rows

    def severity(self, width: float, conf: float, dark: float) -> str:
        score = width * conf * (0.7 + dark)
        if score > 70:
            return "HIGH"
        if score > 35:
            return "MEDIUM"
        return "LOW"
