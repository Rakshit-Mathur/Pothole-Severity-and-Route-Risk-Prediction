from dataclasses import dataclass

import numpy as np


@dataclass
class Frame:
    img: np.ndarray
    t_capture_ns: int
    num: int = 0


@dataclass
class Pose:
    pitch_deg: float
    rate_dps: float
    t_ns: int
    ok: bool = True


@dataclass
class Detection:
    box: tuple[float, float, float, float]
    conf: float
    dark: float = 0.0
