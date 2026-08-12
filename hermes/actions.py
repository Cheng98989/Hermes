"""Gesture names to media keys."""

from typing import NamedTuple

from pynput.keyboard import Controller, Key

from hermes.signals import Repeater


class Action(NamedTuple):
    key: Key
    dwell: float           # seconds to hold before it fires at all
    repeat: float | None   # seconds between repeats, None = fire once


# bound only while in ACTIVE: dwell is how long the gesture must be held
# before it fires, repeat how often it fires again while it is kept up
ACTIONS = {
    "victory":           Action(Key.media_volume_up,   dwell=0.5, repeat=0.30),
    "middle_ring_pinky": Action(Key.media_volume_down, dwell=0.5, repeat=0.30),
    "rock":              Action(Key.media_play_pause,  dwell=0.5, repeat=None),
}


class Actions:
    def __init__(self) -> None:
        self._keyboard = Controller()
        self._repeater = Repeater()

    # returns the gesture that fired, or None
    def update(self, gesture: str, held: float, now: float, enabled: bool) -> str | None:
        action = ACTIONS.get(gesture)
        condition = enabled and action is not None and held >= action.dwell
        interval = action.repeat if action is not None else None

        if self._repeater.should_fire(condition, interval, now) and action is not None:
            self._keyboard.press(action.key)
            self._keyboard.release(action.key)
            return gesture

        return None
