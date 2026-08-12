"""Where the hand is: the point each control follows."""

from hermes.geometry import Point
from hermes.landmarks import INDEX_DIP, KNUCKLES_FOR_CURSOR, MIDDLE_DIP, FrameHands


# drives the pointer: the knuckles are rigid, so the fingers can pinch without
# dragging the cursor sideways
def palm_point(frame: FrameHands) -> Point | None:
    if not frame:
        return None

    hand = frame[0]
    points = [hand[i] for i in KNUCKLES_FOR_CURSOR]
    return Point(
        sum(p.x for p in points) / len(points),
        sum(p.y for p in points) / len(points),
    )


# drives the scroll: far enough from the wrist that a tilt of it is enough,
# so scrolling is a wrist movement instead of an arm one. The DIP joints
# rather than the tips, which are noisier
def finger_point(frame: FrameHands) -> Point | None:
    if not frame:
        return None

    hand = frame[0]
    return Point(
        (hand[INDEX_DIP].x + hand[MIDDLE_DIP].x) / 2,
        (hand[INDEX_DIP].y + hand[MIDDLE_DIP].y) / 2,
    )
