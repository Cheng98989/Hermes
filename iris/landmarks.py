"""How a hand is built, in mediapipe numbering."""

from typing import NewType

# mediapipe returns the same hand twice, in two coordinate systems that are
# structurally identical - both are lists of points with .x, .y and .z - so
# nothing but these two names can tell them apart. Pylance checks them
WorldHands = NewType("WorldHands", list)      # metres, centred on the hand
FrameHands = NewType("FrameHands", list)      # 0..1 across the frame

WRIST = 0

THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4

INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8

MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12

RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16

PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

# the two tips each click watches
LEFT_CLICK_TIPS = (THUMB_TIP, INDEX_TIP)
RIGHT_CLICK_TIPS = (THUMB_TIP, PINKY_TIP)

# the knuckles the pointer follows; the index MCP is left out
KNUCKLES_FOR_CURSOR = (MIDDLE_MCP, RING_MCP)

# every landmark of a finger, knuckle to tip
FINGER_LANDMARKS = {
    "thumb":  (THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP),
    "index":  (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
    "middle": (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
    "ring":   (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
    "pinky":  (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
}

# the hand skeleton, as pairs of connected points
CONNECTIONS = [
    (WRIST, THUMB_CMC), (THUMB_CMC, INDEX_MCP), (INDEX_MCP, MIDDLE_MCP),
    (MIDDLE_MCP, RING_MCP), (RING_MCP, PINKY_MCP), (WRIST, PINKY_MCP),

    (THUMB_CMC, THUMB_MCP), (THUMB_MCP, THUMB_IP), (THUMB_IP, THUMB_TIP),
    (INDEX_MCP, INDEX_PIP), (INDEX_PIP, INDEX_DIP), (INDEX_DIP, INDEX_TIP),
    (MIDDLE_MCP, MIDDLE_PIP), (MIDDLE_PIP, MIDDLE_DIP), (MIDDLE_DIP, MIDDLE_TIP),
    (RING_MCP, RING_PIP), (RING_PIP, RING_DIP), (RING_DIP, RING_TIP),
    (PINKY_MCP, PINKY_PIP), (PINKY_PIP, PINKY_DIP), (PINKY_DIP, PINKY_TIP),
]
