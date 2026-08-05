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

class Repeater:
    """Fires when a condition becomes true, then every `interval` seconds
    while it stays true. interval=None fires only once."""

    def __init__(self) -> None:
        self.last_fire = None    # instant of the last fire; None while inactive

    def should_fire(self, condition: bool, interval: float | None, now: float) -> bool:
        if not condition:                        # 1. condition dropped: re-arm
            self.last_fire = None
            return False

        if self.last_fire is None:            # 2. first frame it is true: fire
            self.last_fire = now
            return True

        if interval is None:                  # 3. one-shot, already fired
            return False

        if now - self.last_fire >= interval:  # 4. time for another one
            self.last_fire = now
            return True

        return False