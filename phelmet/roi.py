import cv2
import numpy as np


def get_horizon(cy: float, focal_px: float, pitch_deg: float) -> int:
    # Pinhole horizon moves upward as the camera points down.
    return int(cy - focal_px * np.tan(np.radians(pitch_deg)))


def pose_ok(pose, cfg: dict) -> bool:
    imu = cfg["imu"]
    return pose.ok and imu["pitch_min"] <= pose.pitch_deg <= imu["pitch_max"] and pose.rate_dps <= imu["max_rate_dps"]


def get_roi(img: np.ndarray, pose, cfg: dict) -> tuple[np.ndarray, int] | None:
    if pose.ok and not pose_ok(pose, cfg):
        return None
    cam = cfg["camera"]
    top = get_horizon(img.shape[0] / 2, cam["focal_px"], pose.pitch_deg) if pose.ok else cfg["roi"]["fixed_top"]
    top = max(0, min(img.shape[0] - 2, top))
    return img[top:], top


def check_road(roi: np.ndarray, cfg: dict) -> bool:
    small = cv2.resize(roi, (96, 72))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].mean()
    texture = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).std()
    edges = cv2.Canny(small, 60, 120).mean() / 255
    c = cfg["roi"]
    return sat >= c["sat_min"] and texture >= c["texture_min"] and edges >= c["edge_min"]


def check_blur(roi: np.ndarray, cfg: dict) -> bool:
    gray = cv2.cvtColor(cv2.resize(roi, (96, 72)), cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() >= cfg["roi"]["blur_min"]
