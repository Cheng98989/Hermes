import cv2
from cv2.typing import MatLike

from hermes.hand import CONNECTIONS

STATE_COLORS = {
        "IDLE":   (0, 0, 255),      # red
        "ACTIVE": (0, 255, 0),      # green
    }

class Overlay:
    """Draws landmarks and debug info on top of a frame"""

    # no defaults: these must come from the camera that actually produced
    # the frame, otherwise every landmark lands in the wrong pixel
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def draw_landmarks(self, frame: MatLike, result) -> None:
        for single_hand in result.hand_landmarks:

            # CONNECTIONS holds (start, end) index pairs, so a and b are
            # positions inside single_hand
            for a, b in CONNECTIONS:
                p1 = single_hand[a]
                p2 = single_hand[b]
                x1, y1 = int(p1.x * self.width), int(p1.y * self.height)
                x2, y2 = int(p2.x * self.width), int(p2.y * self.height)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)

            for point in single_hand:
                x = int(point.x * self.width)
                y = int(point.y * self.height)
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

    def draw_fps(self, frame: MatLike, fps: float) -> None:
        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def draw_text(self, frame: MatLike, text: str, y: int = 70) -> None:
        cv2.putText(
        frame, text, (10, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
        )

    def draw_state_border(self, frame: MatLike, state: str, thickness: int = 8) -> None:
        color = STATE_COLORS.get(state, (128, 128, 128))    # grey for unknown states
        cv2.rectangle(frame, (0, 0), (self.width - 1, self.height - 1), color, thickness) 
