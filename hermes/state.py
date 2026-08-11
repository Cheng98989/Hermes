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

class JoinedFingers:
    """Turns `victory` into `victory_closed` while the two fingers touch.

    The gesture table maps a set of extended fingers onto a name, and "index
    and middle, held together" is not a set - it needs a second measurement.
    Rather than break the shape of that table, the name it produces is refined
    here, one stage later. StateMachine never learns that any of this happened:
    it still receives a name and looks it up.

    Two thresholds, as everywhere a continuous reading becomes a yes/no. With
    one, fingers resting near it would flip the name dozens of times a second,
    and since Hold restarts whenever the name changes, the dwell needed to
    enter SCROLL would never accumulate. The gesture would simply never fire,
    which looks like a broken recogniser rather than a missing threshold.
    """

    def __init__(self, on_below: float, off_above: float) -> None:
        self.switch = Hysteresis(on_below, off_above)

    def update(self, gesture: str, gap: float) -> str:
        # updated every frame, whatever the gesture: a Schmitt trigger that
        # stops being fed freezes, and answers with a stale reading when the
        # gesture comes back
        joined = self.switch.update(gap)

        if gesture == "victory" and joined:
            return "victory_closed"
        return gesture



IDLE = "IDLE"
ACTIVE = "ACTIVE"
CURSOR = "CURSOR"
SCROLL = "SCROLL"

# (current state, gesture) -> (new state, seconds it must be held)
TRANSITIONS = {
    (IDLE,   "open_palm"): (ACTIVE, 1.0),
    (ACTIVE, "fist"):      (IDLE,   1.0),
    (ACTIVE, "none"):      (IDLE,   3.0),
    (ACTIVE, "point"):     (CURSOR, 0.5),
    (CURSOR, "open_palm"): (ACTIVE, 0.5),
    (CURSOR, "none"):      (IDLE,   3.0),
    
    (CURSOR, "victory_closed"): (SCROLL, 0.3),
    (SCROLL, "victory"):        (CURSOR, 0.2),   # apri le dita: esci
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