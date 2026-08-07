"""Turning a stream of noisy per-frame readings into stable answers.

Everything here has the same shape: an object with a memory, fed one reading
per frame, returning something steadier than what went in. They are signal
filters in the proper sense - OneEuroFilter is an adaptive low-pass,
Hysteresis is a Schmitt trigger, Repeater is a debounce, DeadZone is a
Schmitt trigger on a position.

**Nothing in this module knows what a hand is.** It receives numbers,
booleans and instants, and it never reads the clock: main.py reads
perf_counter() once per frame and hands the same value to everyone. That is
what makes all of this testable with made-up data and no webcam.

If something you are about to add here needs to know about fingers, gestures
or states, it belongs in gestures.py or state.py instead.
"""
import math
from collections import deque
from typing import NamedTuple


class Point(NamedTuple):
    """A landmark stripped down to what the rest of the code reads."""

    x: float
    y: float
    z: float


class Hold:
    """How long the value passed in has stayed the same."""

    def __init__(self) -> None:
        self.object = None      # which gesture we are watching
        self.since = 0.0         # the instant it started

    def update(self, object, now: float) -> float:
        if object != self.object:
            self.object = object
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

class Hysteresis:
    """A switch with two thresholds, so a value hovering near the boundary
    cannot flip it back and forth."""

    def __init__(self, on_below: float, off_above: float) -> None:
        if on_below >= off_above:
            raise ValueError(f"on_below ({on_below}) must be less than off_above ({off_above})")
        self.on_below_limit = on_below
        self.off_above_limit = off_above
        self.state = False

    def update(self, value: float) -> bool:
        if value >= self.off_above_limit:
            self.state = False
        if value <= self.on_below_limit:
            self.state = True
        return self.state

class OneEuroFilter:
    """Adaptive low-pass filter described in the One Euro Filter paper.

    Reduces jitter while staying responsive during fast movements.
    Feed one value per frame together with the current timestamp.

    The whole trick is in one line: `cutoff = min_cutoff + beta * speed`.
    Slow movement is filtered hard, fast movement is barely filtered at all,
    so jitter at rest and lag in motion stop being the same dial.

    **beta is in the units of the signal**, which is what makes the paper's
    example numbers useless here. Fed normalised 0..1 coordinates, a fast hand
    moves at 1 to 3 units per second, so a beta of 0.02 - the value this was
    first tried with - raises a 1 Hz cutoff to 1.06 Hz and the adaptation may
    as well not exist. That leaves a plain fixed low-pass: too fast to settle
    at rest, too slow to keep up in motion. Both complaints at once.

    Tuning, in this order and no other:

    1. set beta to 0 and lower min_cutoff until the output is still when the
       input is still
    2. raise beta until the lag during a fast movement stops being felt

    Doing it the other way round tunes beta against jitter it cannot fix.
    """

    def __init__(
        self,
        min_cutoff: float = 0.4,
        beta: float =4.0,
        d_cutoff: float = 1.0,
    ) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

        self.last_time: float | None = None
        self.last_value: float | None = None
        self.last_derivative = 0.0

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    @staticmethod
    def _lerp(alpha: float, value: float, previous: float) -> float:
        return alpha * value + (1.0 - alpha) * previous

    def update(self, value: float, now: float) -> float:
        if self.last_time is None or self.last_value is None:
            self.last_time = now
            self.last_value = value
            return value

        dt = now - self.last_time
        if dt <= 0:
            return self.last_value

        # raw derivative
        derivative = (value - self.last_value) / dt

        # smooth derivative
        alpha_d = self._alpha(self.d_cutoff, dt)
        derivative = self._lerp(alpha_d, derivative, self.last_derivative)

        # adaptive cutoff
        cutoff = self.min_cutoff + self.beta * abs(derivative)

        # smooth value
        alpha = self._alpha(cutoff, dt)
        filtered = self._lerp(alpha, value, self.last_value)

        self.last_time = now
        self.last_value = filtered
        self.last_derivative = derivative

        return filtered

class OneEuroLandmarks:
    """One OneEuroFilter per coordinate of every landmark: 63 in all.

    The tuning is passed in rather than left at the defaults because the two
    instances in main.py are fed different units. The normalised copy drives
    the cursor and is measured in fractions of the frame; the world copy
    drives recognition and is measured in metres. beta scales with the signal,
    so the same number does not mean the same thing to both.
    """

    def __init__(
        self,
        min_cutoff: float = 0.4,
        beta: float = 4.0,
        d_cutoff: float = 1.0,
    ) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self._build()

    def _build(self) -> None:
        """Fresh filters with no memory, keeping the tuning.

        Not `self.__init__()`: that worked only while the settings were
        hardcoded, and would silently throw away whatever this instance was
        constructed with.
        """
        self.filters = [
            tuple(
                OneEuroFilter(self.min_cutoff, self.beta, self.d_cutoff)
                for _ in range(3)
            )
            for _ in range(21)
        ]

    def update(self, hands: list, now: float) -> list:
        if not hands:
            self._build()      # the hand left: forget where it was
            return []

        hand = hands[0]
        filtered = []

        for i, p in enumerate(hand):
            fx, fy, fz = self.filters[i]

            filtered.append(
                Point(
                    fx.update(p.x, now),
                    fy.update(p.y, now),
                    fz.update(p.z, now),
                )
            )

        return [filtered]


class DeadZone:
    """Holds a point still until it moves far enough to mean it.

    Hysteresis in two dimensions, applied to a position instead of a boolean -
    the same shape as the class above, for the same reason.

    It exists because a low-pass filter cannot win this fight alone. Being
    linear, whatever it removes at rest it removes from real movement too: the
    only choice it offers is where to sit on the trade between jitter and lag,
    not how to escape it. This escapes it. Inside the radius the output does
    not move at all, and outside it moves at full speed with nothing added.

    The cost is an offset of up to `radius` while the point is travelling, and
    a slow deliberate movement crawls with the anchor trailing behind it. At
    three or four pixels neither is visible.

    A second thing it buys, free: ARCHITECTURE.md asks that a click must not
    move the pointer, which is why the anchor is a knuckle and not a
    fingertip. The palm still shifts a little as the pinch closes, and that
    shift now falls inside the radius instead of reaching the mouse.

    Works in whatever unit it is fed, but feed it pixels. That is the unit the
    tremor is judged in, and applying it before the zone mapping would both
    scale the radius by 2.5 and turn the circle into an ellipse, since the
    screen is not square.
    """

    def __init__(self, radius: float) -> None:
        self.radius = radius
        self.anchor: tuple[float, float] | None = None

    def update(self, x: float, y: float) -> tuple[float, float]:
        if self.anchor is None:
            self.anchor = (x, y)
            return self.anchor

        anchor_x, anchor_y = self.anchor
        dx, dy = x - anchor_x, y - anchor_y
        distance = math.hypot(dx, dy)

        if distance > self.radius:
            # drag the anchor along, leaving it `radius` behind the new point
            keep = (distance - self.radius) / distance
            self.anchor = (anchor_x + dx * keep, anchor_y + dy * keep)

        return self.anchor

    def reset(self) -> None:
        """Forget the anchor, so the pointer appears wherever the hand comes
        back rather than crawling there from where it was left."""
        self.anchor = None


class Wander:
    """How still a point is. A tuning instrument, not part of the pipeline.

    Reports two numbers over a sliding window, in whatever unit it is fed:

    - `step`: the largest jump between one frame and the next. This is the
      shimmer - fast and small, and the part a low-pass filter can remove.
    - `spread`: the largest excursion across the whole window. This is slow
      drift, which no filter that judges by speed can tell from a real slow
      movement, so it survives any amount of low-passing.

    Hold the hand still and read them in pixels. `step` says whether
    min_cutoff is low enough; `spread` says how big the dead zone has to be to
    swallow what is left.
    """

    def __init__(self, window: int = 60) -> None:
        self.points = deque(maxlen=window)
        self.steps = deque(maxlen=window)

    def update(self, x: float, y: float) -> tuple[float, float]:
        if self.points:
            previous_x, previous_y = self.points[-1]
            self.steps.append(math.hypot(x - previous_x, y - previous_y))
        self.points.append((x, y))

        xs = [point[0] for point in self.points]
        ys = [point[1] for point in self.points]
        spread = max(max(xs) - min(xs), max(ys) - min(ys))
        step = max(self.steps) if self.steps else 0.0
        return step, spread

    def reset(self) -> None:
        self.points.clear()
        self.steps.clear()