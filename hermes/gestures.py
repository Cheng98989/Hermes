"""Turning hand landmarks into gesture names.

Everything here works on mediapipe's **world landmarks** - real 3D positions
in metres, centred on the hand - not on the normalised image coordinates.

That distinction is the whole reason this module works. Measured on this
machine, moving and tilting a hand made the projected palm length swing by a
factor of 8 (0.10 to 0.80), while the same measure in world coordinates
stayed within 30% (0.09 to 0.12 m - a real palm). Image coordinates are a
shadow: they change when the hand merely turns. World coordinates describe
the hand itself.

The module imports nothing but `math`, so it can be tested without a webcam.
"""

import math

WRIST = 0
MIDDLE_KNUCKLE = 9

# name -> (tip, middle knuckle)
#
# The thumb is deliberately absent. It folds sideways rather than curling, and
# in a natural fist it rests on the outside of the other fingers - far enough
# out to pass any "is it extended?" test we tried. That made a plain fist
# register as a thumb gesture, and the fist is what switches Hermes off.
# Four fingers that are always right beat five with one that lies.
# Worth retrying now that measurements happen in 3D.
FINGERS = {
    "index":  (8, 6),
    "middle": (12, 10),
    "ring":   (16, 14),
    "pinky":  (20, 18),
}

# Counting fingers is the most reliable thing the recogniser does, so the
# vocabulary is built on it rather than on where the hand points. Orientation
# was tried and dropped: it needs the hand held at a definite angle, which is
# uncomfortable at a desk and fragile to detect.
GESTURES = {
    frozenset():                                      "fist",
    frozenset({"index"}):                             "point",
    frozenset({"index", "middle"}):                   "victory",
    frozenset({"index", "middle", "ring"}):           "three",
    
    frozenset({"index", "pinky"}):                    "rock",
    frozenset({"index", "middle", "ring", "pinky"}):  "open_palm",
}


def distance(a, b) -> float:
    """Distance between two landmarks, in three dimensions."""
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))


def palm_size(hand) -> float:
    """Wrist to middle knuckle, in metres.

    The one length that never changes whatever the fingers do, and - unlike
    its projected counterpart - not when the hand tilts either. Around 0.09
    to 0.12 on the hand this was measured with.
    """
    return distance(hand[WRIST], hand[MIDDLE_KNUCKLE])


def fingers_up(hand) -> set[str]:
    """Which fingers are extended.

    A finger is extended when its tip is farther from the wrist than its
    middle knuckle. No thresholds anywhere: every test compares two
    distances, so hand size cancels out.
    """
    up_fingers = set()
    for finger, (tip, middle) in FINGERS.items():
        tip_distance = distance(hand[tip], hand[WRIST])
        knuckle_distance = distance(hand[middle], hand[WRIST])
        if tip_distance > knuckle_distance:
            up_fingers.add(finger)

    return up_fingers


def gesture_name(hand) -> str:
    """Name of the recognised gesture, or 'unknown' if this combination of
    extended fingers is not in the table."""
    return GESTURES.get(frozenset(fingers_up(hand)), "unknown")


def gesture_from_hands(hands) -> str:
    """hands is result.hand_world_landmarks: an empty list when no hand is in
    frame."""
    if not hands:
        return "none"
    return gesture_name(hands[0])
