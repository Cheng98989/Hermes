from pynput.keyboard import Controller, Key
from typing import NamedTuple
from hermes.filters import Repeater


class Action(NamedTuple):
    key: Key
    dwell: float           # seconds to hold before it fires at all
    repeat: float | None   # seconds between repeats, None = fire once


# One finger down, two fingers up: counting is what the recogniser does best,
# so the commands ride on that rather than on the angle of the hand.
#
# open_palm and fist are missing on purpose - they switch Hermes on and off,
# and the dwell here is shorter than the one the state machine uses, so an
# action bound to either would fire at the very moment of switching.
# "victory_closed" is deliberately absent, and putting it back would be a
# mistake. JoinedFingers splits two fingers up into two gestures, and each one
# now means a different thing: apart is the volume, together is scrolling. One
# pose, one meaning.
#
# Binding both spellings to the volume looks like a kindness - the user gets
# their volume whatever the fingers are doing - but it turns every pass
# through the scrolling pose into a possible volume command, which is a false
# positive on the way out of a state rather than a feature.
ACTIONS = {
    "victory": Action(Key.media_volume_up,   dwell=0.5, repeat=0.30),
    "middle_ring_pinky": Action(Key.media_volume_down,   dwell=0.5, repeat=0.30),
    "rock":    Action(Key.media_play_pause,  dwell=0.5, repeat=None),
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