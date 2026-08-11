"""Turning the height of a hand into scrolling.

Rate control, not position control: the hand's distance from an origin sets
the *speed* of scrolling, not the amount. Position control - the hand dragging
the page like a touchscreen - was rejected because the arm runs out of travel
after a few centimetres, and a long page would need a clutch gesture to
re-grip with. With a rate there is no travel limit: the hand sits still at an
offset and the page keeps moving.

The module reads no clock and knows nothing about hands. It receives a height,
an instant, and returns whole scroll clicks.
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
            # first frame in this state: wherever the hand is means "stopped"
            self.origin = y
            self.last_time = now
            return 0

        dt = min(now - self.last_time, self.max_dt)
        self.last_time = now
        if dt <= 0:
            return 0

        return self._accumulate(self._rate(y), dt)

    def _rate(self, y: float) -> float:
        """Clicks per second for a hand at this height. Sign included."""
        # normalised y grows downwards, so the origin comes first: a hand
        # ABOVE the origin has to produce a positive number
        if self.origin is None:
            return 0
        offset = self.origin - y

        # the dead zone is subtracted before normalising, so speed leaves the
        # zone at zero. Dividing first would make it jump straight to whatever
        # the boundary was worth
        magnitude = (abs(offset) - self.dead_zone) / (self.span - self.dead_zone)
        magnitude = min(max(magnitude, 0.0), 1.0)

        # squared: flat near the middle, so small deliberate offsets give fine
        # control, and steep at the edges where you want to cover a page
        rate = self.max_rate * magnitude ** 2
        return rate if offset > 0 else -rate

    def _accumulate(self, rate: float, dt: float) -> int:
        """Whole clicks owed, keeping the fraction for next time.

        The mouse only accepts whole clicks. At 30 fps a rate of 3 clicks per
        second is 0.1 of a click per frame, and truncating that on its own
        every frame returns zero forever - the page would never move at any
        speed below one click per frame.

        int() and not floor(): int truncates towards zero, so the same code
        works in both directions. floor(-0.5) is -1, which would fire a click
        upwards half a click early and make the two directions behave
        differently.
        """
        self.carry += rate * dt
        clicks = int(self.carry)
        self.carry -= clicks
        return clicks

    def reset(self) -> None:
        """Leaving the state: forget the origin, so coming back re-centres on
        wherever the hand is, and drop the fraction so it cannot leak a stray
        click into the next session."""
        self.origin = None
        self.last_time = None
        self.carry = 0.0