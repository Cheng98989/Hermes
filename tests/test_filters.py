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

from hermes.filters import Hold, Repeater


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
