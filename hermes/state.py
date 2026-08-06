from hermes.filters import Hold, Hysteresis


class DragTracker:
    """Two phases: strict to start dragging, permissive to keep dragging."""

    def __init__(self, on_below=0.25, off_above=0.40, dwell=0.1) -> None:
        self.switch = Hysteresis(on_below, off_above)
        self.hold = Hold()
        self.dwell = dwell
        self.dragging = False

    def update(self, pinch_distance: float, guard_ok: bool, now: float) -> bool:
        pinched = self.switch.update(pinch_distance)
        ready = pinched and guard_ok
        held = self.hold.update(ready, now)
        if self.dragging:
            if pinched is False:
                self.dragging = False
        elif ready and held >= self.dwell:
            self.dragging = True
        return self.dragging




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