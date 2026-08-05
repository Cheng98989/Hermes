"""Tests for hermes.state.

=============================================================================
GENERATED FILE - this entire file was written by Claude (Anthropic) on
2026-08-05, on request. See the header of test_gestures.py for how the rest
of the project was built.
=============================================================================

Not a single sleep() in here. GestureHold and StateMachine never read the
clock: main.py reads it once per frame and passes the instant in. That is
what lets a test say "held for 1.1 seconds" by passing the number 1.1,
instead of actually waiting.
"""

import pytest

from hermes.state import ACTIVE, IDLE, GestureHold, StateMachine


# --- GestureHold ------------------------------------------------------------

def test_a_new_gesture_starts_at_zero():
    hold = GestureHold()
    assert hold.update("open_palm", 10.0) == 0.0


def test_the_same_gesture_accumulates_time():
    # pytest.approx, not ==: floats are approximate, and 11.2 - 10.0 comes
    # out as 1.1999999999999993
    hold = GestureHold()
    hold.update("open_palm", 10.0)
    assert hold.update("open_palm", 10.5) == pytest.approx(0.5)
    assert hold.update("open_palm", 11.2) == pytest.approx(1.2)


def test_changing_gesture_resets_the_clock():
    hold = GestureHold()
    hold.update("open_palm", 10.0)
    hold.update("open_palm", 11.5)
    assert hold.update("fist", 11.6) == 0.0


def test_going_back_to_a_gesture_does_not_resume_it():
    """Holding is continuous: letting go and coming back starts over."""
    hold = GestureHold()
    hold.update("open_palm", 0.0)
    hold.update("open_palm", 0.9)     # almost there
    hold.update("none", 1.0)          # hand drops for one frame
    assert hold.update("open_palm", 1.1) == 0.0


# --- StateMachine -----------------------------------------------------------

def test_starts_idle():
    assert StateMachine().state == IDLE


def test_open_palm_held_long_enough_activates():
    machine = StateMachine()
    assert machine.update("open_palm", 1.0) == ACTIVE


def test_open_palm_held_too_briefly_does_nothing():
    machine = StateMachine()
    assert machine.update("open_palm", 0.9) == IDLE


def test_an_unrelated_gesture_is_ignored():
    machine = StateMachine()
    assert machine.update("victory", 5.0) == IDLE


def test_the_same_gesture_means_something_else_once_active():
    """open_palm switches Hermes on, but means nothing while it is already
    on - there is no rule for (ACTIVE, open_palm)."""
    machine = StateMachine()
    machine.update("open_palm", 1.0)
    assert machine.update("open_palm", 5.0) == ACTIVE


def test_fist_held_long_enough_deactivates():
    machine = StateMachine()
    machine.update("open_palm", 1.0)
    assert machine.update("fist", 1.0) == IDLE


def test_losing_the_hand_deactivates_after_the_timeout():
    machine = StateMachine()
    machine.update("open_palm", 1.0)
    assert machine.update("none", 2.9) == ACTIVE
    assert machine.update("none", 3.0) == IDLE


def test_a_brief_gap_does_not_deactivate():
    """The hand dipping out of frame for a moment must not switch Hermes
    off - only a sustained absence does."""
    machine = StateMachine()
    machine.update("open_palm", 1.0)
    assert machine.update("none", 1.5) == ACTIVE


# --- the two together -------------------------------------------------------

def test_full_sequence():
    """A plausible run: noise, activation, noise while active, shutdown."""
    hold = GestureHold()
    machine = StateMachine()

    frames = [
        (0.0, "none"),
        (0.2, "victory"),      # noise
        (0.4, "unknown"),      # noise
        (0.6, "open_palm"),
        (1.4, "open_palm"),    # 0.8s held: not yet
        (1.7, "open_palm"),    # 1.1s held: switches on
        (2.0, "victory"),      # means nothing yet
        (3.0, "fist"),
        (4.1, "fist"),         # 1.1s held: switches off
    ]
    states = [machine.update(g, hold.update(g, t)) for t, g in frames]

    assert states == [
        IDLE, IDLE, IDLE, IDLE, IDLE,
        ACTIVE, ACTIVE, ACTIVE,
        IDLE,
    ]
