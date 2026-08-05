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

from hermes.gestures import (
    FINGERS,
    GESTURES,
    fingers_up,
    gesture_from_hands,
    gesture_name,
    palm_size,
)

# Fake hand geometry in world-landmark space: metres, origin near the middle
# of the hand, y growing downwards. The hand points up, so a finger is
# "extended" when its tip sits farther from the wrist than its knuckle.
# The numbers are roughly life-size: about 7 cm wrist to knuckle.
WRIST_POS = (0.00, 0.05, 0.00)
KNUCKLE_POS = (0.00, -0.02, 0.00)
TIP_UP_POS = (0.00, -0.09, 0.00)     # farther from the wrist than the knuckle
TIP_DOWN_POS = (0.00, 0.02, 0.00)    # curled back towards the palm


class FakeLandmark:
    """Stand-in for mediapipe's Landmark: only x, y and z are read."""

    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.z = z


def make_hand(extended: set[str]) -> list[FakeLandmark]:
    """Build 21 fake landmarks with the named fingers extended."""
    hand = [FakeLandmark(*WRIST_POS) for _ in range(21)]

    # the MCP knuckles, where the fingers meet the palm. Not used by
    # fingers_up, but palm_size measures the wrist to landmark 9, so leaving
    # them sitting on the wrist would make the palm zero metres long.
    for mcp in (5, 9, 13, 17):
        hand[mcp] = FakeLandmark(*KNUCKLE_POS)

    for name, (tip, knuckle) in FINGERS.items():
        hand[knuckle] = FakeLandmark(*KNUCKLE_POS)
        hand[tip] = FakeLandmark(
            *(TIP_UP_POS if name in extended else TIP_DOWN_POS)
        )

    return hand


# --- fingers_up -------------------------------------------------------------

def test_closed_fist_has_no_extended_fingers():
    assert fingers_up(make_hand(set())) == set()


def test_single_finger():
    assert fingers_up(make_hand({"index"})) == {"index"}


def test_two_fingers():
    assert fingers_up(make_hand({"index", "middle"})) == {"index", "middle"}


def test_open_hand():
    every_finger = {"index", "middle", "ring", "pinky"}
    assert fingers_up(make_hand(every_finger)) == every_finger


def test_the_thumb_is_never_reported():
    """The thumb was dropped on purpose: in a natural fist it rests outside
    the other fingers and reads as extended, which made a plain fist - the
    gesture that switches Hermes off - register as something else."""
    assert "thumb" not in fingers_up(make_hand({"index", "middle"}))


def test_counting_comes_free_from_the_set():
    assert len(fingers_up(make_hand({"index", "middle", "ring"}))) == 3


# --- palm_size --------------------------------------------------------------

def test_the_palm_is_a_plausible_length():
    """World landmarks are metres, so this should look like a real hand.
    Guards against the fake hand drifting into nonsense."""
    assert 0.03 < palm_size(make_hand(set())) < 0.20


def test_the_palm_does_not_change_when_the_fingers_move():
    """That is the whole reason palm_size uses the wrist and a knuckle:
    it is the one length a hand cannot change."""
    closed = palm_size(make_hand(set()))
    open_hand = palm_size(make_hand({"index", "middle", "ring", "pinky"}))
    assert closed == pytest.approx(open_hand)


# --- gesture_name -----------------------------------------------------------

@pytest.mark.parametrize(
    "extended,expected",
    [(set(combination), name) for combination, name in GESTURES.items()],
)
def test_every_gesture_in_the_table_is_recognised(extended, expected):
    """One case per row of GESTURES, generated from the table itself: add a
    gesture there and it gets tested automatically."""
    assert gesture_name(make_hand(extended)) == expected


def test_combination_outside_the_table_is_unknown():
    """Most hand positions are not gestures - while the hand moves, almost
    every frame is one of them. This must not raise.

    Middle and ring together is an awkward pose nobody would bind a command
    to, which is what makes it a safe example here. If it ever ends up in
    GESTURES this test will fail and want a different one.
    """
    absent = {"middle", "ring"}
    assert frozenset(absent) not in GESTURES, "pick a combination still unused"
    assert gesture_name(make_hand(absent)) == "unknown"


# --- gesture_from_hands -----------------------------------------------------

def test_no_hand_in_frame_is_a_gesture_of_its_own():
    """"none" is not the same as "unknown": no hand at all is what the safety
    timeout watches for, while "unknown" means the hand is there but doing
    something unrecognised."""
    assert gesture_from_hands([]) == "none"


def test_the_first_hand_is_the_one_that_counts():
    assert gesture_from_hands([make_hand({"index", "middle"})]) == "victory"
