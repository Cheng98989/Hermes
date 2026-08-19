"""The states Hermes can be in, and the trackers that feed them."""

from collections.abc import Callable

from hermes.signals import Hold, Hysteresis, Repeater
from hermes.config import IDLE, ACTIVE, CURSOR, SCROLL, STATES
from hermes.recognition import (
    FIST,
    NONE,
    OPEN_PALM,
    PINKY_PINCH,
    POINT,
    VICTORY,
    VICTORY_CLOSED,
)

# (current state, gesture) -> (new state, seconds it must be held).
TRANSITIONS = {
    (IDLE,   OPEN_PALM): (ACTIVE, 1.0),
    (ACTIVE, FIST):      (IDLE,   1.0),
    (ACTIVE, NONE):      (IDLE,   2.0),
    (ACTIVE, POINT):     (CURSOR, 0.5),
    (CURSOR, OPEN_PALM): (ACTIVE, 0.5),
    (CURSOR, NONE):      (IDLE,   2.0),

    (CURSOR, VICTORY_CLOSED): (SCROLL, 0.3),
    (SCROLL, VICTORY):        (CURSOR, 0.2),   # open the fingers to leave
    (SCROLL, POINT):          (CURSOR, 0.2),
    (SCROLL, OPEN_PALM):      (ACTIVE, 0.5),
    (SCROLL, NONE):           (IDLE,   2.0),
}


class StateMachine:
    def __init__(self, on_change) -> None:
        self.state = IDLE
        self.on_change = on_change

    def update(self, gesture: str, held: float) -> str:
        found = TRANSITIONS.get((self.state, gesture))
        if found is not None:
            new_state, required = found
            if held >= required:
                self._change_state(new_state)

        return self.state

    def set_state(self, state: str) -> None:
        if state not in STATES:
            raise ValueError(f"unknown state: {state}")
        self._change_state(state)

    # only a real move rings: the camera-lost branch forces IDLE every frame
    def _change_state(self, state: str) -> None:
        if state == self.state:
            return

        self.state = state
        self.on_change(state)


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


class RightClickTracker:
    def __init__(self) -> None:
        self.repeater = Repeater()

    def update(self, gesture: str, now: float) -> bool:
        return self.repeater.should_fire(gesture == PINKY_PINCH, None, now)


class JoinedFingers:
    def __init__(self, on_below: float, off_above: float) -> None:
        self.switch = Hysteresis(on_below, off_above)

    def update(self, gesture: str, gap: float, when: str, becomes: str) -> str:
        # every frame, whatever the gesture: a switch that stops being fed
        # freezes, and answers with a stale reading later
        joined = self.switch.update(gap)

        if gesture == when and joined:
            return becomes

        return gesture
