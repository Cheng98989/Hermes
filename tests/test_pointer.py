"""Tests for the pointer chain: palm_point and DeadZone.

=============================================================================
GENERATED FILE - written by Claude (Anthropic) on 2026-08-07, on request.
See the header of test_gestures.py for how the rest of the project was built.
=============================================================================

Everything under test here is pure, so the numbers are made up and no webcam
is involved. Where a test uses pixels it says so: the dead zone is the one
piece deliberately expressed in screen units rather than normalised ones.
"""

import math

import pytest

from hermes.filters import DeadZone
from hermes.gestures import ANCHOR_POINTS, palm_point


class FakeLandmark:
    """Stand-in for mediapipe's Landmark: only x, y and z are read."""

    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


def make_hand(**overrides) -> list[FakeLandmark]:
    """21 landmarks all at the origin, with named ones moved somewhere.

    Starting from zero makes the arithmetic in these tests readable: only the
    points that matter carry a value.
    """
    hand = [FakeLandmark(0.0, 0.0) for _ in range(21)]
    for index, (x, y) in overrides.items():
        hand[int(index[1:])] = FakeLandmark(x, y)
    return hand


# --- palm_point -------------------------------------------------------------

def test_no_hand_leaves_the_pointer_alone():
    """None rather than a default position: the caller must be able to tell
    "no reading" from "a reading that happens to be the origin"."""
    assert palm_point([]) is None


def test_it_averages_exactly_the_four_knuckles():
    hand = make_hand(p5=(0.2, 0.4), p9=(0.4, 0.4), p13=(0.6, 0.8), p17=(0.8, 0.8))
    assert palm_point([hand]) == pytest.approx((0.5, 0.6))


def test_the_wrist_is_not_part_of_it():
    """Landmark 0 is rigid too, but including it would drag the anchor down
    the hand - and the wrist was rejected as an anchor for that reason."""
    knuckles = {"p5": (0.4, 0.4), "p9": (0.4, 0.4), "p13": (0.4, 0.4), "p17": (0.4, 0.4)}
    without_wrist = palm_point([make_hand(**knuckles)])
    with_a_wild_wrist = palm_point([make_hand(**knuckles, p0=(0.9, 0.9))])
    assert without_wrist == with_a_wild_wrist == pytest.approx((0.4, 0.4))


def test_moving_the_fingers_does_not_move_the_anchor():
    """The whole reason for anchoring here. Every fingertip and joint swings
    wildly; the pointer must not notice."""
    knuckles = {"p5": (0.3, 0.5), "p9": (0.4, 0.5), "p13": (0.5, 0.5), "p17": (0.6, 0.5)}
    fist = make_hand(**knuckles)
    spread = make_hand(**knuckles)
    for tip in (4, 8, 12, 16, 20, 6, 7, 10, 11):
        spread[tip] = FakeLandmark(0.95, 0.05)

    assert palm_point([fist]) == pytest.approx(palm_point([spread]))


def test_averaging_shrinks_independent_noise():
    """Not a proof, a demonstration of the point of the class: the same jitter
    applied to four landmarks lands smaller on their mean than on any one of
    them. Signs chosen to cancel, which is the case averaging exists for."""
    jitter = {"p5": (0.30 + 0.01, 0.5), "p9": (0.40 - 0.01, 0.5),
              "p13": (0.50 + 0.01, 0.5), "p17": (0.60 - 0.01, 0.5)}
    clean = {"p5": (0.30, 0.5), "p9": (0.40, 0.5), "p13": (0.50, 0.5), "p17": (0.60, 0.5)}

    assert palm_point([make_hand(**jitter)]) == pytest.approx(palm_point([make_hand(**clean)]))


def test_it_reads_the_documented_landmarks():
    """ANCHOR_POINTS is the MCP row. If someone edits it, this says so."""
    assert ANCHOR_POINTS == (5, 9, 13, 17)


# --- DeadZone ---------------------------------------------------------------

def test_the_first_reading_is_taken_as_it_comes():
    """Nothing to be still relative to yet, so the anchor starts where the
    pointer starts rather than at some arbitrary place."""
    zone = DeadZone(radius=3.0)
    assert zone.update(100.0, 200.0) == (100.0, 200.0)


def test_jitter_inside_the_radius_moves_nothing():
    """The reason the class exists. Four frames of tremor, all under three
    pixels, and the pointer is bit-for-bit where it started."""
    zone = DeadZone(radius=3.0)
    zone.update(100.0, 100.0)
    for dx, dy in ((2.0, 0.0), (-2.0, 1.0), (0.0, -2.5), (1.5, 1.5)):
        assert zone.update(100.0 + dx, 100.0 + dy) == (100.0, 100.0)


def test_the_boundary_itself_does_not_move_it():
    """Exactly `radius` away is still inside: > and not >=, so a value resting
    precisely on the edge cannot chatter."""
    zone = DeadZone(radius=3.0)
    zone.update(0.0, 0.0)
    assert zone.update(3.0, 0.0) == (0.0, 0.0)


def test_crossing_the_radius_drags_the_anchor_along():
    """Moving 10 px with a 3 px radius leaves the anchor 3 px behind."""
    zone = DeadZone(radius=3.0)
    zone.update(0.0, 0.0)
    assert zone.update(10.0, 0.0) == pytest.approx((7.0, 0.0))


def test_it_trails_by_the_radius_and_never_more():
    """A long fast movement must not accumulate lag: the offset is a constant
    3 px, not something that grows with distance travelled."""
    zone = DeadZone(radius=3.0)
    zone.update(0.0, 0.0)
    for x in range(0, 500, 20):
        anchor_x, _ = zone.update(float(x), 0.0)
        assert 0.0 <= x - anchor_x <= 3.0 + 1e-9


def test_the_radius_is_a_circle_not_a_square():
    """3 px right and 3 px up is 4.24 px away, which is outside a radius of 3.
    A per-axis test would wrongly call this still."""
    zone = DeadZone(radius=3.0)
    zone.update(0.0, 0.0)
    moved = zone.update(3.0, 3.0)
    assert moved != (0.0, 0.0)
    assert math.hypot(*moved) == pytest.approx(math.hypot(3.0, 3.0) - 3.0)


def test_reset_makes_the_pointer_appear_rather_than_crawl():
    """Without this, a hand that left on one side and came back on the other
    would drag the pointer across the screen three pixels at a time."""
    zone = DeadZone(radius=3.0)
    zone.update(0.0, 0.0)
    zone.reset()
    assert zone.update(900.0, 500.0) == (900.0, 500.0)
