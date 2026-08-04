from collections import deque
import time


class FpsCounter:
    """Measures frames per second.

    Call tick() exactly once per loop iteration.
    """

    def __init__(self, window: int = 30) -> None:
        self.durations = deque(maxlen=window)
        self.last_time = time.perf_counter()

    def tick(self) -> float:
        now = time.perf_counter()
        self.durations.append(now - self.last_time)
        self.last_time = now
        return len(self.durations) / sum(self.durations) if self.durations else 0