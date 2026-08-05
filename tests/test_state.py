"""Tests for hermes.state.

=============================================================================
GENERATED FILE - written by Claude (Anthropic) on 2026-08-05, on request.
See the header of test_gestures.py for how the rest of the project was built.
=============================================================================

StateMachine takes the hold time as a number, so every scenario here is just
a list of (instant, gesture) pairs. No webcam, no clock, no waiting.
"""

from hermes.state import ACTIVE, IDLE, StateMachine
from hermes.timing import GestureHold


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
        (2.0, "victory"),      # means nothing to the state machine
        (3.0, "fist"),
        (4.1, "fist"),         # 1.1s held: switches off
    ]
    states = [machine.update(g, hold.update(g, t)) for t, g in frames]

    assert states == [
        IDLE, IDLE, IDLE, IDLE, IDLE,
        ACTIVE, ACTIVE, ACTIVE,
        IDLE,
    ]
