"""What the hand is doing: world landmarks in, a gesture name out."""

import math

from hermes.geometry import distance_2d, distance_3d
from hermes.landmarks import (
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

# extended fingers -> gesture name
GESTURES = {
    frozenset():                                      "fist",
    frozenset({"index"}):                             "point",
    frozenset({"index", "middle"}):                   "victory",
    frozenset({"index", "middle", "ring"}):           "three",
    frozenset({"middle", "ring", "pinky"}):           "middle_ring_pinky",
    frozenset({"index", "pinky"}):                    "rock",
    frozenset({"index", "ring", "pinky"}):            "rock_with_ring",
    frozenset({"index", "middle", "ring", "pinky"}):  "open_palm",
}


# a finger is extended when its tip is farther from the wrist than its joint
def fingers_up(hand) -> set[str]:
    up_fingers = set()
    for finger, (tip, joint) in FINGERS.items():
        if distance_3d(hand[tip], hand[WRIST]) > distance_3d(hand[joint], hand[WRIST]):
            up_fingers.add(finger)

    return up_fingers


def gesture_name(hand) -> str:
    return GESTURES.get(frozenset(fingers_up(hand)), "unknown")


# "none" when no hand is in frame
def gesture_from_hands(world: WorldHands) -> str:
    if not world:
        return "none"

    return gesture_name(world[0])


# --- pinch ------------------------------------------------------------------

# fingers that must be closed for a pinch to count; the index is not checked
GUARD_FINGERS = {"middle", "ring", "pinky"}


def pinch_distance(world: WorldHands) -> float:
    if not world:
        return math.inf

    hand = world[0]
    return distance_2d(hand[THUMB_TIP], hand[INDEX_TIP]) / palm_size(hand)


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
