import math

WRIST = 0

# name -> (tip, middle knuckle)
# the thumb is not here: it folds sideways, so the generic rule below
# does not work for it
FINGERS = {
    "index":  (8, 6),
    "middle": (12, 10),
    "ring":   (16, 14),
    "pinky":  (20, 18),
}

THUMB_TIP = 4
THUMB_KNUCKLE = 2
MIDDLE_KNUCKLE = 9
PINKY_KNUCKLE = 17

GESTURES = {
    frozenset()                                           : "fist",
    frozenset({"index"})                                  : "point",
    frozenset({"index", "middle"})                        : "victory",
    frozenset({"thumb"})                                  : "thumb_up",
    frozenset({"thumb", "index"})                         : "gun",
    frozenset({"index", "pinky"})                         : "rock",
    frozenset({"thumb", "index", "middle", "ring", "pinky"}): "open_palm",
    frozenset({"thumb", "index", "pinky"})                : "spiderman",
}

def _distance(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def palm_size(hand) -> float:
    """Wrist to middle knuckle.

    Careful: this is a 2D projection, so it shrinks when the hand tilts
    towards the camera. Measured values collapsed towards zero on some
    frames, which is why nothing here divides by it any more. Kept because
    it is still a reasonable scale reference for gestures that need one.
    """
    return _distance(hand[WRIST], hand[MIDDLE_KNUCKLE])


def _thumb_up(hand) -> bool:
    """Same rule as the other four fingers - tip farther away than knuckle -
    but measured from the pinky knuckle instead of the wrist.

    The thumb rotates around a pivot that sits right next to the wrist, so
    from the wrist its tip appears to stay at the same distance whatever it
    does. From the opposite side of the palm the rotation is visible.
    """
    tip_distance = _distance(hand[THUMB_TIP], hand[PINKY_KNUCKLE])
    knuckle_distance = _distance(hand[THUMB_KNUCKLE], hand[PINKY_KNUCKLE])
    return tip_distance > knuckle_distance


def fingers_up(hand) -> set[str]:
    """Which fingers are extended.

    A finger is extended when its tip is farther from the wrist than its
    middle knuckle. No thresholds anywhere: every test compares two
    distances, so hand size and camera distance cancel out.
    """
    up_fingers = set()
    for finger, (tip, middle) in FINGERS.items():
        tip_distance = _distance(hand[tip], hand[WRIST])
        knuckle_distance = _distance(hand[middle], hand[WRIST])
        if tip_distance > knuckle_distance:
            up_fingers.add(finger)

    if _thumb_up(hand):
        up_fingers.add("thumb")

    return up_fingers

def gesture_name(hand) -> str:
    """Name of the recognised gesture, or 'unknown' if this combination
    of extended fingers is not in the table."""
    return GESTURES.get(frozenset(fingers_up(hand)), "unknown")

def gesture_from_hands(hands) -> str:
    """hands is result.hand_landmarks: an empty list when no hand is in frame."""
    if not hands:
        return "none"
    return gesture_name(hands[0])