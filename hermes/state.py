class GestureHold:
    """Tracks how long the current gesture has been held."""

    def __init__(self) -> None:
        self.gesture = None      # which gesture we are watching
        self.since = 0.0         # the instant it started

    def update(self, gesture: str, now: float) -> float:
        if gesture != self.gesture:
            self.gesture = gesture
            self.since = now
            return 0.0
        return now - self.since