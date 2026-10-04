import math


def get_distance(bottom_y: float, cy: float, focal_px: float,
                 height_m: float, pitch_deg: float) -> float | None:
    """Ground ray: distance = camera height / tan(downward ray angle)."""
    angle = math.atan((bottom_y - cy) / focal_px) + math.radians(pitch_deg)
    if angle <= 0.01:
        return None
    return height_m / math.tan(angle)


def get_width_cm(box_w: float, distance_m: float, focal_px: float) -> float:
    return box_w * distance_m / focal_px * 100.0


def get_tti(distance_m: float, speed_mps: float) -> float | None:
    if speed_mps <= 0.1:
        return None
    return distance_m / speed_mps
