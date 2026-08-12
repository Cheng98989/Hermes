"""Hand height to scroll clicks.

Rate control, not position: the distance from an origin sets the scroll
*speed*, so a long page needs no re-grip.
"""


class ScrollRate:
    def __init__(
        self,
        dead_zone: float = 0.03,
        span: float = 0.18,
        max_rate: float = 12.0,
        max_dt: float = 0.1,
    ) -> None:
        self.dead_zone = dead_zone      # no scrolling within this of the origin
        self.span = span                # offset at which max_rate is reached
        self.max_rate = max_rate        # clicks per second, flat out
        self.max_dt = max_dt            # longest frame that will be believed

        self.origin: float | None = None
        self.last_time: float | None = None
        self.carry = 0.0

    def update(self, y: float, now: float) -> int:
        if self.origin is None or self.last_time is None:
            self.origin = y
            self.last_time = now
            return 0

        dt = min(now - self.last_time, self.max_dt)
        self.last_time = now
        if dt <= 0:
            return 0

        return self._accumulate(self._rate(y), dt)

    # clicks per second at this height, sign included
    def _rate(self, y: float) -> float:
        if self.origin is None:
            return 0.0

        offset = self.origin - y

        # the dead zone is subtracted before dividing, so speed leaves it at
        # zero instead of jumping to whatever the boundary was worth
        dead_zone_stack = (abs(offset) - self.dead_zone) / (self.span - self.dead_zone)
        dead_zone_stack = min(max(dead_zone_stack, 0.0), 1.0)

        # squared: fine scroll control near the middle, quick at the edges
        rate = self.max_rate * dead_zone_stack ** 2
        return rate if offset > 0 else -rate

    # whole clicks owed, keeping the fraction for next time: the mouse takes
    # only whole ones, and truncating each frame alone would return zero forever
    def _accumulate(self, rate: float, dt: float) -> int:
        self.carry += rate * dt
        clicks = int(self.carry)
        self.carry -= clicks
        return clicks

    def reset(self) -> None:
        self.origin = None
        self.last_time = None
        self.carry = 0.0
