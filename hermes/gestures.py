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

# The four MCP knuckles: the points that do not move when the fingers do.
#
# The wrist is just as rigid and is deliberately left out. It sits far enough
# down the hand that averaging it in would drag the anchor towards it, and the
# wrist was already rejected as an anchor for exactly that reason - with the
# anchor that low, reaching the edge of the active zone takes the fingers out
# of frame. The centre of these four lands next to landmark 9, so the active
# zone stays tuned the way it was.
ANCHOR_POINTS = (5, 9, 13, 17)

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
    frozenset({"middle", "ring", "pinky"}):           "middle_ring_pinky",

    frozenset({"index", "pinky"}):                    "rock",
    frozenset({"index", "ring", "pinky"}):            "rock_with_ring",
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
    """Whether the hand is in the posture a pinch is allowed from: middle,
    ring and pinky all closed.

    That is the shape a hand already has while pointing, so the guard costs
    nothing to satisfy on purpose and rejects the half-open poses a hand
    passes through on its way somewhere else.

    The index is not checked. While pinching it bends to reach the thumb, so
    whether it counts as extended depends on the angle - an unreliable thing
    to gate on.
    """
    if not hands:
        return False

    guarded = fingers_up(hands[0]) & GUARD_FINGERS
    return not guarded


def palm_point(hands) -> tuple[float, float] | None:
    """Where the pointer should be: the centre of the palm, 0..1 across the frame.

    The four MCP knuckles averaged, rather than knuckle 9 on its own. They are
    all rigid - none of them move when the fingers do - so averaging them is a
    spatial mean, not a temporal one, and costs no lag whatsoever. What it
    buys is the cancellation of part of the noise mediapipe puts on each
    landmark independently.

    That noise is worth more than it looks. The active zone is half the frame
    wide and covers the whole screen, so on a 1920px monitor one normalised
    unit is 3840 pixels, and 0.001 of jitter is four pixels of visible
    tremor. The anchor is the one number in the pipeline amplified like
    that.

    Averaging only pays to the extent the noise is independent between
    landmarks, and mediapipe regresses the whole hand in one pass, so expect
    rather less than the factor of two the arithmetic promises. Measure it.

    Returns None when no hand is in frame, so the caller can leave the pointer
    where it is rather than move it somewhere arbitrary.
    """
    if not hands:
        return None

    hand = hands[0]
    points = [hand[i] for i in ANCHOR_POINTS]
    return (
        sum(p.x for p in points) / len(points),
        sum(p.y for p in points) / len(points),
    )