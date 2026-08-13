"""Signal conditioning: noisy per-frame readings to steady answers."""

import math

from hermes.geometry import Point, distance_2d


# --- time -------------------------------------------------------------------

# how long the value passed in has stayed the same
class Hold:
    def __init__(self) -> None:
        self.object = None
        self.since = 0.0

    def update(self, object, now: float) -> float:
        if object != self.object:
            self.object = object
            self.since = now
            return 0.0

        return now - self.since


# fires when a condition becomes true, then every `interval` while it holds;
# interval=None fires once
class Repeater:
    def __init__(self) -> None:
        self.last_fire = None

    def should_fire(self, condition: bool, interval: float | None, now: float) -> bool:
        if not condition:
            self.last_fire = None
            return False

        if self.last_fire is None:
            self.last_fire = now
            return True

        if interval is None:
            return False

        if now - self.last_fire >= interval:
            self.last_fire = now
            return True

        return False


# --- turning a continuous reading into a decision ---------------------------

# a switch with two thresholds, so a value near the boundary cannot flip it
class Hysteresis:
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


# the same idea applied to a position: holds a point still until it moves far
# enough to mean it.
class DeadZone:
    def __init__(self, radius: float) -> None:
        self.radius = radius
        self.anchor: Point | None = None

    def update(self, target: Point) -> Point:
        if self.anchor is None:
            self.anchor = target
            return self.anchor

        distance = distance_2d(self.anchor, target)

        # > and not >=, so a value resting exactly on the edge cannot chatter
        if distance > self.radius:
            # drag the anchor along, leaving it `radius` behind the new point
            keep = (distance - self.radius) / distance
            self.anchor = Point(
                self.anchor.x + (target.x - self.anchor.x) * keep,
                self.anchor.y + (target.y - self.anchor.y) * keep,
            )

        return self.anchor

    def reset(self) -> None:
        self.anchor = None


# --- smoothing --------------------------------------------------------------

# alpha for a first-order low-pass: derived from a cutoff in Hz and the real
# frame time, so the same tuning behaves the same at any frame rate
def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


def _lerp(alpha: float, value: float, previous: float) -> float:
    return alpha * value + (1.0 - alpha) * previous


# adaptive low-pass: filters hard when the signal is slow, barely at all when
# it is fast, so jitter at rest and lag in motion stop being the same dial.
# beta is in the units of the signal and does not carry between filters
class OneEuroFilter:
    def __init__(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.reset()

    def reset(self) -> None:
        self.last_time: float | None = None
        self.last_value: float | None = None
        self.last_derivative = 0.0

    def update(self, value: float, now: float) -> float:
        if self.last_time is None or self.last_value is None:
            self.last_time = now
            self.last_value = value
            return value

        dt = now - self.last_time
        if dt <= 0:
            return self.last_value

        # the derivative is smoothed too, at a fixed cutoff: differentiating
        # amplifies noise, and an unfiltered speed would make the cutoff below
        # chase it instead of the hand
        derivative = (value - self.last_value) / dt
        derivative = _lerp(_alpha(self.d_cutoff, dt), derivative, self.last_derivative)

        cutoff = self.min_cutoff + self.beta * abs(derivative)
        filtered = _lerp(_alpha(cutoff, dt), value, self.last_value)

        self.last_time = now
        self.last_value = filtered
        self.last_derivative = derivative

        return filtered


# one OneEuroFilter per coordinate of every landmark: 63 in all, each its own
# signal. The tuning lives in the filters, so this class only routes
class OneEuroLandmarks:
    def __init__(self, min_cutoff: float, beta: float, d_cutoff: float = 1.0) -> None:
        self.filters = [
            tuple(OneEuroFilter(min_cutoff, beta, d_cutoff) for _ in range(3))
            for _ in range(21)
        ]

    def reset(self) -> None:
        for axes in self.filters:
            for one_euro in axes:
                one_euro.reset()

    def update(self, hands: list, now: float) -> list:
        if not hands:
            self.reset()      # the hand left: forget where it was
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
