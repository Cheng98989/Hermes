"""Drawing on the preview frame."""

import cv2
from cv2.typing import MatLike

from iris.geometry import XY
from iris.landmarks import CONNECTIONS

# BGRs
WHITE = (255, 255, 255)
GREY = (170, 170, 170)
YELLOW = (0, 255, 255)
ORANGE = (0, 165, 255)
CYAN = (255, 255, 0)
RED = (0, 0, 255)

# degub texts colors
LINE_COLOURS = {
    "FPS": CYAN,
    "Gesture": WHITE,
    "Pinch": ORANGE,
    "Fingers": ORANGE,
    "Command": YELLOW,
    "Pointer": GREY,
}

FONT = cv2.FONT_HERSHEY_SIMPLEX
SCALE = 0.55
THICKNESS = 1
MARGIN = 12
FIRST_LINE = 30
LINE_HEIGHT = 24


class Overlay:
    def __init__(
        self,
        stream_width: int,
        stream_height: int,
        state_colors: dict[str, list[int]],
    ) -> None:
        self.width = stream_width
        self.height = stream_height
        self.state_colors: dict[str, tuple[int, ...]] = {}
        for state, color in state_colors.items():
            self.state_colors[state] = tuple(color)
        self.unknown_color = self.state_colors.get("UNKNOWN", (128, 128, 128))
        self._next_y = FIRST_LINE

    def _to_frame(self, point: XY) -> tuple[int, int]:
        return int(point.x * self.width), int(point.y * self.height)

    def draw_landmarks(self, frame: MatLike, hands) -> None:
        for single_hand in hands:
            for a, b in CONNECTIONS:
                cv2.line(frame, self._to_frame(single_hand[a]), self._to_frame(single_hand[b]),
                         (255, 255, 255), 1)

            for point in single_hand:
                cv2.circle(frame, self._to_frame(point), 2, (0, 255, 0), -1)

    def start_lines(self) -> None:
        self._next_y = FIRST_LINE

    def draw_line(self, frame: MatLike, label: str, value: str, colour=None) -> None:
        colour = colour or LINE_COLOURS.get(label, WHITE)
        cv2.putText(frame, f"{label:<9}{value}", (MARGIN, self._next_y),
                    FONT, SCALE, colour, THICKNESS, cv2.LINE_AA)
        self._next_y += LINE_HEIGHT

    # its own size and colour
    def draw_paused(self, frame: MatLike) -> None:
        cv2.putText(frame, "PAUSED", (MARGIN, self.height - MARGIN),
                    FONT, 1.0, RED, 2, cv2.LINE_AA)

    def state_colour(self, state: str) -> tuple[int, ...]:
        return self.state_colors.get(state, self.unknown_color)

    # the border shows which state Iris is in
    def draw_state_border(self, frame: MatLike, state: str, thickness: int = 8) -> None:
        color = self.state_colour(state)
        cv2.rectangle(frame, (0, 0), (self.width - 1, self.height - 1), color, thickness)

    # the part of the camera view that reaches the screen
    def draw_mouse_mapping_area(self, frame: MatLike, zone_min: float, zone_max: float) -> None:
        x1, y1 = int(self.width * zone_min), int(self.height * zone_min)
        x2, y2 = int(self.width * zone_max), int(self.height * zone_max)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

    # the height that means stopped, and the band around it: the origin is
    def draw_scroll_origin(self, frame: MatLike, origin_y: float | None, dead_zone: float) -> None:
        if origin_y is None:
            return

        y = int(origin_y * self.height)
        band = int(dead_zone * self.height)
        cv2.line(frame, (0, y), (self.width, y), (0, 255, 255), 1)
        cv2.rectangle(frame, (0, y - band), (self.width - 1, y + band), (0, 255, 255), 1)
