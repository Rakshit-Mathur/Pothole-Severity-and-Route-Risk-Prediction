import time
from collections import deque

import numpy as np


def now_ns() -> int:
    return time.monotonic_ns()


class Timer:
    def __init__(self) -> None:
        self.start_ns = now_ns()

    def ms(self) -> float:
        return (now_ns() - self.start_ns) / 1_000_000


class Rolling:
    def __init__(self, count: int = 200) -> None:
        self.vals = deque(maxlen=count)

    def add(self, value: float) -> None:
        self.vals.append(value)

    def p50(self) -> float:
        return self._pct(50)

    def p95(self) -> float:
        return self._pct(95)

    def _pct(self, n: int) -> float:
        return float(np.percentile(self.vals, n)) if self.vals else 0.0
