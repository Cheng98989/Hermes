"""Tests for hermes.filters.

=============================================================================
GENERATED FILE - written by Claude (Anthropic) on 2026-08-05, on request.
See the header of test_gestures.py for how the rest of the project was built.
=============================================================================

Not a single sleep() in here. Nothing in filters.py reads the clock: main.py
reads it once per frame and passes the instant in. That is what lets a test
say "held for 1.1 seconds" by passing the number 1.1.
"""

import pytest

from hermes.filters import Hold, Repeater, Smoothed, SmoothedLandmarks


# --- GestureHold ------------------------------------------------------------

def test_a_new_gesture_starts_at_zero():
    hold = Hold()
    assert hold.update("open_palm", 10.0) == 0.0


def test_the_same_gesture_accumulates_time():
    # pytest.approx, not ==: floats are approximate, and 11.2 - 10.0 comes
    # out as 1.1999999999999993
    hold = Hold()
    hold.update("open_palm", 10.0)
    assert hold.update("open_palm", 10.5) == pytest.approx(0.5)
    assert hold.update("open_palm", 11.2) == pytest.approx(1.2)


def test_changing_gesture_resets_the_clock():
    hold = Hold()
    hold.update("open_palm", 10.0)
    hold.update("open_palm", 11.5)
    assert hold.update("fist", 11.6) == 0.0


def test_going_back_to_a_gesture_does_not_resume_it():
    """Holding is continuous: letting go and coming back starts over."""
    hold = Hold()
    hold.update("open_palm", 0.0)
    hold.update("open_palm", 0.9)     # almost there
    hold.update("none", 1.0)          # hand drops for one frame
    assert hold.update("open_palm", 1.1) == 0.0


# --- Repeater, one-shot mode (interval=None) --------------------------------

def test_a_false_condition_never_fires():
    rep = Repeater()
    assert rep.should_fire(False, None, 0.0) is False
    assert rep.should_fire(False, None, 5.0) is False


def test_it_fires_the_moment_the_condition_becomes_true():
    rep = Repeater()
    rep.should_fire(False, None, 0.0)
    assert rep.should_fire(True, None, 0.1) is True


def test_one_shot_does_not_fire_again_while_held():
    """This is the whole point: at 30 fps a gesture held for a second would
    otherwise send thirty keystrokes."""
    rep = Repeater()
    assert rep.should_fire(True, None, 0.0) is True
    fires = [rep.should_fire(True, None, t / 30) for t in range(1, 31)]
    assert not any(fires)


def test_releasing_and_holding_again_fires_again():
    rep = Repeater()
    rep.should_fire(True, None, 0.0)
    rep.should_fire(False, None, 1.0)      # condition drops: re-arms
    assert rep.should_fire(True, None, 1.1) is True


# --- Repeater, repeat mode --------------------------------------------------

def test_repeat_fires_immediately_then_waits():
    rep = Repeater()
    assert rep.should_fire(True, 0.15, 0.00) is True
    assert rep.should_fire(True, 0.15, 0.10) is False    # too soon
    assert rep.should_fire(True, 0.15, 0.15) is True     # due


def test_repeat_keeps_going_while_held():
    """Volume up held for a second should step up several times, not once."""
    rep = Repeater()
    fires = sum(rep.should_fire(True, 0.15, t / 30) for t in range(31))
    assert fires == 7      # one at t=0, then every 150 ms for one second


def test_repeat_stops_when_the_condition_drops():
    rep = Repeater()
    rep.should_fire(True, 0.15, 0.0)
    assert rep.should_fire(False, 0.15, 0.2) is False
    assert rep.should_fire(False, 0.15, 0.4) is False


# --- Smoothed ---------------------------------------------------------------

def test_the_first_value_is_reported_as_it_arrives():
    smoothed = Smoothed(window=5)
    assert smoothed.update("victory") == "victory"


def test_a_lone_stray_frame_is_outvoted():
    """The whole reason the class exists: mediapipe guessing wrong for one
    frame out of five must not change the recognised gesture."""
    smoothed = Smoothed(window=5)
    for _ in range(4):
        smoothed.update("fist")
    assert smoothed.update("victory") == "fist"


def test_a_sustained_change_wins_after_a_few_frames():
    """A deliberate new gesture fills the window and takes the majority.
    At 30 fps the three frames below are a tenth of a second."""
    smoothed = Smoothed(window=5)
    for _ in range(5):
        smoothed.update("fist")
    assert smoothed.update("victory") == "fist"       # four fists to one
    assert smoothed.update("victory") == "fist"       # three to two
    assert smoothed.update("victory") == "victory"    # two to three: it turns


def test_values_older_than_the_window_stop_counting():
    smoothed = Smoothed(window=3)
    smoothed.update("fist")
    smoothed.update("fist")
    smoothed.update("victory")
    # the first fist has just fallen out of the window, leaving one fist
    # against two victories - with a longer window the fists would still win
    assert smoothed.update("victory") == "victory"


# --- SmoothedLandmarks ------------------------------------------------------

class FakeLandmark:
    """Stand-in for mediapipe's Landmark: only x, y and z are read."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


def make_hand(offset: float = 0.0) -> list[FakeLandmark]:
    """21 landmarks, each at a different place so that mixing two of them up
    would show. `offset` shifts the whole hand, standing in for it moving."""
    return [
        FakeLandmark(0.01 * i + offset, 0.02 * i + offset, 0.03 * i + offset)
        for i in range(21)
    ]


def coords(hand) -> list[float]:
    """Flatten a hand into plain numbers, so a whole hand fits in a single
    pytest.approx - which does not handle nested structures."""
    return [c for point in hand for c in (point.x, point.y, point.z)]


def test_a_single_frame_comes_back_unchanged():
    """Nothing to average against yet, so the mean of one frame is itself."""
    smoothed = SmoothedLandmarks(window=5)
    result = smoothed.update([make_hand()])
    assert len(result) == 1
    assert len(result[0]) == 21
    assert coords(result[0]) == pytest.approx(coords(make_hand()))


def test_every_coordinate_is_the_mean_of_the_frames_so_far():
    smoothed = SmoothedLandmarks(window=5)
    smoothed.update([make_hand(0.0)])
    smoothed.update([make_hand(0.3)])
    result = smoothed.update([make_hand(0.3)])
    # (0.0 + 0.3 + 0.3) / 3 = 0.2, on every one of the 63 numbers
    assert coords(result[0]) == pytest.approx(coords(make_hand(0.2)))


def test_frames_older_than_the_window_stop_counting():
    smoothed = SmoothedLandmarks(window=2)
    smoothed.update([make_hand(0.0)])
    smoothed.update([make_hand(1.0)])
    result = smoothed.update([make_hand(3.0)])
    # the first frame has dropped out: (1.0 + 3.0) / 2, not (0 + 1 + 3) / 3
    assert coords(result[0]) == pytest.approx(coords(make_hand(2.0)))


def test_no_hand_in_frame_gives_no_hand_back():
    smoothed = SmoothedLandmarks(window=5)
    smoothed.update([make_hand()])
    assert smoothed.update([]) == []


def test_a_hand_coming_back_is_not_dragged_towards_where_it_was():
    """An empty frame clears the history. Otherwise a hand that left one side
    of the picture and reappeared on the other would be averaged with its own
    past for several frames, and read as somewhere in between."""
    smoothed = SmoothedLandmarks(window=5)
    for _ in range(4):
        smoothed.update([make_hand(0.0)])
    smoothed.update([])
    result = smoothed.update([make_hand(1.0)])
    assert coords(result[0]) == pytest.approx(coords(make_hand(1.0)))


def test_only_the_first_hand_comes_back():
    """Everything downstream reads hands[0], so the second hand is dropped
    here rather than smoothed and then ignored."""
    smoothed = SmoothedLandmarks(window=5)
    result = smoothed.update([make_hand(0.0), make_hand(5.0)])
    assert len(result) == 1
    assert coords(result[0]) == pytest.approx(coords(make_hand(0.0)))


def test_the_averaged_landmarks_still_look_like_landmarks():
    """gestures.py reads .x, .y and .z off whatever comes out of here, so the
    averaged points have to carry those attributes, not just the numbers."""
    smoothed = SmoothedLandmarks(window=5)
    point = smoothed.update([make_hand()])[0][5]
    assert (point.x, point.y, point.z) == pytest.approx((0.05, 0.10, 0.15))
