from collections import deque


class FpsCounter:
    """Measures frames per second.

    Call tick() exactly once per loop iteration.
    """

    def __init__(self, now: float, window: int = 30) -> None:
        self.durations = deque(maxlen=window)
        self.last_time = now

    def tick(self, now: float) -> float:
        self.durations.append(now - self.last_time)
        self.last_time = now
        return len(self.durations) / sum(self.durations) if self.durations else 0