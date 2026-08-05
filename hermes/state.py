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

IDLE = "IDLE"
ACTIVE = "ACTIVE"

# (current state, gesture) -> (new state, seconds it must be held)
TRANSITIONS = {
    (IDLE,   "open_palm"): (ACTIVE, 1.0),
    (ACTIVE, "fist"):      (IDLE,   1.0),
    (ACTIVE, "none"):      (IDLE,   3.0),
}


class StateMachine:
    def __init__(self) -> None:
        self.state = IDLE

    def update(self, gesture: str, held: float) -> str:
        found = TRANSITIONS.get((self.state, gesture))
        if found is not None:
            new_state, required = found
            if held >= required:
                self.state = new_state

        return self.state

class EdgeTrigger:
    """Fires once when a condition becomes true, not while it stays true."""

    def __init__(self) -> None:
        self.was_true = False

    def rising(self, condition: bool) -> bool:
        fire = condition and not self.was_true
        self.was_true = condition
        return fire