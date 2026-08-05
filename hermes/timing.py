from collections import Counter, deque
from typing import NamedTuple


class Point(NamedTuple):
    """A landmark stripped down to what the rest of the code reads."""

    x: float
    y: float
    z: float


class SmoothedLandmarks:
    """Averages every landmark position over the last few frames.

    Applied straight after detection, so everything downstream - curl,
    distances, directions, and any measure not invented yet - works on clean
    numbers. Smoothing here rather than inside gestures.py keeps that module
    pure: it has no memory of previous frames and stays testable with made-up
    data.

    Smoothing the numbers beats smoothing the decisions. Once a value has
    been compared against a threshold, 0.58 and 0.62 have become "down" and
    "up" - two opposite answers - and no amount of voting recovers the fact
    that they were the same reading with a little noise on it.
    """

    def __init__(self, window: int = 5) -> None:
        self.frames = deque(maxlen=window)

    def update(self, hands: list) -> list:
        """Takes result.hand_world_landmarks, returns the same shape with the
        first hand averaged. Only the first hand is smoothed, because it is
        the only one anything reads."""
        if not hands:
            # the hand left: drop the history, or when it comes back the
            # average would drag it towards where it used to be
            self.frames.clear()
            return []

        hand = hands[0]
        self.frames.append([Point(p.x, p.y, p.z) for p in hand])

        count = len(self.frames)
        averaged = [
            Point(
                sum(frame[i].x for frame in self.frames) / count,
                sum(frame[i].y for frame in self.frames) / count,
                sum(frame[i].z for frame in self.frames) / count,
            )
            for i in range(len(hand))
        ]
        return [averaged]


class Smoothed:
    """Reports the most common of the last few values instead of the latest.

    mediapipe has to guess where fingers it cannot see are - in a fist they
    are hidden behind the palm and behind each other - and those guesses jump
    from one frame to the next. A single stray frame changed the recognised
    gesture, which reset the hold timer, which meant a command could never
    build up enough time to fire.

    Taking the majority of a short window ignores strays while keeping real
    changes: a deliberate new gesture fills the window in a few frames.
    """

    def __init__(self, window: int = 5) -> None:
        self.values = deque(maxlen=window)

    def update(self, value: str) -> str:
        self.values.append(value)
        return Counter(self.values).most_common(1)[0][0]


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