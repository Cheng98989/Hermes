"""What the hand is doing: world landmarks in, a gesture name out."""

import math

from iris.geometry import distance_2d, distance_3d
from iris.landmarks import (
    INDEX_DIP,
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_DIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_PIP,
    PINKY_TIP,
    RING_PIP,
    RING_TIP,
    THUMB_TIP,
    WRIST,
    WorldHands,
)


# wrist to middle knuckle, in metres: the one length the fingers cannot change
def palm_size(hand) -> float:
    return distance_3d(hand[WRIST], hand[MIDDLE_MCP])


# --- which fingers are up, and what that pose is called ----------------------

# the two points whose distance from the wrist is compared. The thumb is
# deliberately absent.
FINGERS = {
    "index":  (INDEX_TIP, INDEX_PIP),
    "middle": (MIDDLE_TIP, MIDDLE_PIP),
    "ring":   (RING_TIP, RING_PIP),
    "pinky":  (PINKY_TIP, PINKY_PIP),
}

# gestures vocabulary
NONE = "none"
UNKNOWN = "unknown"
FIST = "fist"
POINT = "point"
VICTORY = "victory"
THREE = "three"
MIDDLE_RING_PINKY = "middle_ring_pinky"
ROCK = "rock"
ROCK_WITH_RING = "rock_with_ring"
OPEN_PALM = "open_palm"
VICTORY_CLOSED = "victory_closed"
PINKY_PINCH = "pinky_pinch"
PINKY_READY = "pinky_ready"

# extended fingers -> gesture name
GESTURES = {
    frozenset():                                      FIST,
    frozenset({"index"}):                             POINT,
    frozenset({"index", "middle"}):                   VICTORY,
    frozenset({"index", "middle", "ring"}):           THREE,
    frozenset({"middle", "ring", "pinky"}):           MIDDLE_RING_PINKY,
    frozenset({"index", "pinky"}):                    ROCK,
    frozenset({"index", "ring", "pinky"}):            ROCK_WITH_RING,
    frozenset({"index", "middle", "ring", "pinky"}):  OPEN_PALM,
}


# a finger is extended when its tip is farther from the wrist than its joint
def fingers_up(hand) -> set[str]:
    up_fingers = set()
    for finger, (tip, joint) in FINGERS.items():
        if distance_3d(hand[tip], hand[WRIST]) > distance_3d(hand[joint], hand[WRIST]):
            up_fingers.add(finger)

    return up_fingers


def gesture_name(hand) -> str:
    return GESTURES.get(frozenset(fingers_up(hand)), UNKNOWN)


# NONE when no hand is in frame
def gesture_from_hands(world: WorldHands) -> str:
    if not world:
        return NONE

    return gesture_name(world[0])


# --- pinch ------------------------------------------------------------------

# fingers that must be closed for a pinch to count; the index is not checked
GUARD_FINGERS = {"middle", "ring", "pinky"}


def pinch_distance(world: WorldHands, tip_a: int, tip_b: int) -> float:
    if not world:
        return math.inf

    hand = world[0]
    return distance_2d(hand[tip_a], hand[tip_b]) / palm_size(hand)


def pinch_guard_ok(world: WorldHands) -> bool:
    if not world:
        return False

    return not (fingers_up(world[0]) & GUARD_FINGERS)


# --- scroll -----------------------------------------------------------------

def finger_gap(world: WorldHands) -> float:
    if not world:
        return math.inf

    hand = world[0]
    return distance_2d(hand[INDEX_DIP], hand[MIDDLE_DIP]) / palm_size(hand)
