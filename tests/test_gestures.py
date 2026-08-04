"""Tests for hermes.gestures.

=============================================================================
GENERATED FILE - this entire file was written by Claude (Anthropic) on
2026-08-05, on request, as a worked example of what a pytest suite looks
like.

The rest of the project was built with Claude acting as a tutor: the design
was reasoned out together, the code was typed by hand, and Claude corrected
mistakes and rewrote passages along the way. So other files are not free of
its input either - this one is simply the only one generated outright.
=============================================================================

No webcam, no mediapipe, no model file: fingers_up() only ever reads .x and
.y from each landmark, so a plain object with those two attributes is enough
to stand in for a real one. That is exactly why gestures.py was kept free of
I/O - it is the only module that can be tested this way.

Run from the project root:

    .venv\\Scripts\\python -m pytest
"""

import pytest

from hermes.gestures import FINGERS, GESTURES, fingers_up, gesture_name

# Fake hand geometry. The hand points up, so a finger is "extended" when its
# tip sits higher on screen (smaller y) than its knuckle. Values are in the
# 0..1 normalised space mediapipe uses.
WRIST_POS = (0.50, 0.90)
KNUCKLE_POS = (0.50, 0.70)
TIP_UP_POS = (0.50, 0.50)      # farther from the wrist than the knuckle
TIP_DOWN_POS = (0.50, 0.85)    # curled back towards the palm

PINKY_KNUCKLE_POS = (0.60, 0.70)   # landmark 17, the thumb's reference point
THUMB_KNUCKLE_POS = (0.42, 0.75)   # landmark 2
THUMB_OUT_POS = (0.25, 0.72)       # spread away from the palm
THUMB_IN_POS = (0.55, 0.72)        # folded across the palm


class FakeLandmark:
    """Stand-in for mediapipe's NormalizedLandmark: only x and y are read."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


def make_hand(extended: set[str]) -> list[FakeLandmark]:
    """Build 21 fake landmarks with the named fingers extended."""
    hand = [FakeLandmark(*WRIST_POS) for _ in range(21)]

    for name, (tip, knuckle) in FINGERS.items():
        hand[knuckle] = FakeLandmark(*KNUCKLE_POS)
        hand[tip] = FakeLandmark(*(TIP_UP_POS if name in extended else TIP_DOWN_POS))

    hand[17] = FakeLandmark(*PINKY_KNUCKLE_POS)
    hand[2] = FakeLandmark(*THUMB_KNUCKLE_POS)
    hand[4] = FakeLandmark(*(THUMB_OUT_POS if "thumb" in extended else THUMB_IN_POS))

    return hand


# --- fingers_up -------------------------------------------------------------

def test_closed_fist_has_no_extended_fingers():
    assert fingers_up(make_hand(set())) == set()


def test_single_finger():
    assert fingers_up(make_hand({"index"})) == {"index"}


def test_two_fingers():
    assert fingers_up(make_hand({"index", "middle"})) == {"index", "middle"}


def test_thumb_on_its_own():
    """The thumb uses a different rule from the other four, so it gets its
    own test: it must be detected without dragging any other finger along."""
    assert fingers_up(make_hand({"thumb"})) == {"thumb"}


def test_open_hand():
    every_finger = {"thumb", "index", "middle", "ring", "pinky"}
    assert fingers_up(make_hand(every_finger)) == every_finger


def test_counting_comes_free_from_the_set():
    assert len(fingers_up(make_hand({"index", "middle", "ring"}))) == 3


# --- gesture_name -----------------------------------------------------------

@pytest.mark.parametrize(
    "extended,expected",
    [(set(combination), name) for combination, name in GESTURES.items()],
)
def test_every_gesture_in_the_table_is_recognised(extended, expected):
    """One test per row of GESTURES, generated from the table itself: add a
    gesture there and it gets tested automatically."""
    assert gesture_name(make_hand(extended)) == expected


def test_combination_outside_the_table_is_unknown():
    """Most hand positions are not gestures - while the hand moves, almost
    every frame is one of them. This must not raise."""
    assert gesture_name(make_hand({"index", "middle", "ring"})) == "unknown"
