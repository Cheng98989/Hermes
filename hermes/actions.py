from pynput.keyboard import Controller, Key
from typing import NamedTuple
from hermes.timing import Repeater


class Action(NamedTuple):
    key: Key
    dwell: float           # seconds to hold before it fires at all
    repeat: float | None   # seconds between repeats, None = fire once


ACTIONS = {
    "thumb_up":   Action(Key.media_volume_up,   dwell=0.3, repeat=0.15),
    "thumb_down": Action(Key.media_volume_down, dwell=0.3, repeat=0.15),
    "victory":    Action(Key.media_play_pause,  dwell=0.5, repeat=None),
}


class Actions:
    """Turns a gesture name into a keystroke on the real system."""

    def __init__(self) -> None:
        self._keyboard = Controller()
        self._repeater = Repeater()

    def update(self, gesture: str, held: float, now: float, enabled: bool) -> str | None:
        action = ACTIONS.get(gesture)
        condition = enabled and action is not None and held >= action.dwell
        interval = action.repeat if action is not None else None

        if self._repeater.should_fire(condition, interval, now) and action is not None:
            self._keyboard.press(action.key)
            self._keyboard.release(action.key)
            return gesture
        return None