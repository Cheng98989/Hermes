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
THUMB_TIP = 4
INDEX_TIP = 8
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

def distance_2d(a, b) -> float:
    """Distance in the image plane, ignoring depth."""
    return math.hypot(a.x - b.x, a.y - b.y)

def distance_3d(a, b) -> float:
    """Distance between two landmarks, in three dimensions."""
    return math.dist((a.x, a.y, a.z), (b.x, b.y, b.z))

def palm_size(hand) -> float:
    """Wrist to middle knuckle, in metres.

    The one length that never changes whatever the fingers do, and - unlike
    its projected counterpart - not when the hand tilts either. Around 0.09
    to 0.12 on the hand this was measured with.
    """
    return distance_3d(hand[WRIST], hand[MIDDLE_KNUCKLE])

def pinch_distance(hands) -> float:
    """How close the thumb and index tips are, in palm lengths.

    NOTE: this is the one measurement in the module that uses distance_2d
    while everything else uses distance_3d. Deliberate, not an oversight -
    please do not "fix" it.

    z is the only coordinate mediapipe estimates rather than observes - one
    camera cannot see depth - and it is the first thing to degrade at an
    awkward angle. For a pinch it is pure noise: if two tips are touching
    they are in the same place in the image, which x and y report directly.
    Measured here, "fingers touching" ranged 0.1 to 0.5 in 3D and overlapped
    with "fingers apart"; in 2D it stays at 0.1 to 0.2 against 0.9 for an
    open hand.

    There is no universally better choice between 2D and 3D - only the right
    measurement for the question being asked. Whether a finger is extended is
    about shape in space, so it needs 3D. Whether two tips touch is about
    where they appear, so it needs the image.

    The known weakness: seen edge-on, thumb and index can overlap in the
    image without touching. It takes deliberate aiming to trigger, and a
    pinch only ever means anything while Hermes is already ACTIVE.

    Returns infinity when no hand is in frame - as far apart as fingers can
    possibly be - so anything watching this releases instead of latching.
    """
    if not hands:
        return math.inf

    hand = hands[0]
    return distance_2d(hand[THUMB_TIP], hand[INDEX_TIP]) / palm_size(hand)

def fingers_up(hand) -> set[str]:
    """Which fingers are extended.

    A finger is extended when its tip is farther from the wrist than its
    middle knuckle. No thresholds anywhere: every test compares two
    distances, so hand size cancels out.
    """
    up_fingers = set()
    for finger, (tip, middle) in FINGERS.items():
        tip_distance = distance_3d(hand[tip], hand[WRIST])
        knuckle_distance = distance_3d(hand[middle], hand[WRIST])
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

GUARD_FINGERS = {"middle", "ring", "pinky"}

def pinch_guard_ok(hands) -> bool:
    """Whether the fingers not involved in the pinch are in a definite
    position - all extended or all closed, never halfway."""
    if not hands:
        return False
    fingers = fingers_up(hands[0])
    guarded = fingers & GUARD_FINGERS
    return guarded == GUARD_FINGERS or not guarded
