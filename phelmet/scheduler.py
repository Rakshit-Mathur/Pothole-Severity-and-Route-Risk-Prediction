class Scheduler:
    def __init__(self, limit_ms: float) -> None:
        self.limit = limit_ms
        self.skip = False
        self.n = 0

    def should_run(self) -> bool:
        self.n += 1
        return not self.skip or self.n % 2 == 0

    def update(self, p95: float) -> None:
        if not self.skip and p95 > self.limit:
            self.skip = True
            print("adaptive skip on")
        elif self.skip and p95 < self.limit * 0.75:
            self.skip = False
            print("adaptive skip off")
