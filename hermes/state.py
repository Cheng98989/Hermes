"""The states Hermes can be in, and the trackers that feed them."""

from hermes.signals import Hold, Hysteresis

IDLE = "IDLE"
ACTIVE = "ACTIVE"
CURSOR = "CURSOR"
SCROLL = "SCROLL"

STATES = {IDLE, ACTIVE, CURSOR, SCROLL}

# (current state, gesture) -> (new state, seconds it must be held).
TRANSITIONS = {
    (IDLE,   "open_palm"): (ACTIVE, 1.0),
    (ACTIVE, "fist"):      (IDLE,   1.0),
    (ACTIVE, "none"):      (IDLE,   3.0),
    (ACTIVE, "point"):     (CURSOR, 0.5),
    (CURSOR, "open_palm"): (ACTIVE, 0.5),
    (CURSOR, "none"):      (IDLE,   3.0),

    (CURSOR, "victory_closed"): (SCROLL, 0.3),
    (SCROLL, "victory"):        (CURSOR, 0.2),   # open the fingers to leave
    (SCROLL, "point"):          (CURSOR, 0.2),
    (SCROLL, "open_palm"):      (ACTIVE, 0.5),
    (SCROLL, "none"):           (IDLE,   3.0),
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

    def set_state(self, state: str) -> None:
        if state not in STATES:
            raise ValueError(f"unknown state: {state}")
        self.state = state


class DragTracker:
    def __init__(self, on_below: float, off_above: float, dwell: float) -> None:
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


class JoinedFingers:
    def __init__(self, on_below: float, off_above: float) -> None:
        self.switch = Hysteresis(on_below, off_above)

    def update(self, gesture: str, gap: float) -> str:
        # every frame, whatever the gesture: a switch that stops being fed
        # freezes, and answers with a stale reading later
        joined = self.switch.update(gap)

        if gesture == "victory" and joined:
            return "victory_closed"

        return gesture
