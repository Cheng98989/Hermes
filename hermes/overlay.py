"""Drawing on the preview frame."""

import cv2
from cv2.typing import MatLike

from hermes.geometry import XY
from hermes.landmarks import CONNECTIONS


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

    def _to_frame(self, point: XY) -> tuple[int, int]:
        return int(point.x * self.width), int(point.y * self.height)

    def draw_landmarks(self, frame: MatLike, hands) -> None:
        for single_hand in hands:
            for a, b in CONNECTIONS:
                cv2.line(frame, self._to_frame(single_hand[a]), self._to_frame(single_hand[b]),
                         (255, 255, 255), 1)

            for point in single_hand:
                cv2.circle(frame, self._to_frame(point), 2, (0, 255, 0), -1)

    def draw_fps(self, frame: MatLike, fps: float) -> None:
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def draw_text(self, frame: MatLike, text: str, y: int = 70) -> None:
        cv2.putText(frame, text, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # the border shows which state Hermes is in
    def draw_state_border(self, frame: MatLike, state: str, thickness: int = 8) -> None:
        color = self.state_colors.get(state, self.unknown_color)
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
