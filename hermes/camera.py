"""The webcam: open, read, mirror, close."""

import cv2
from cv2.typing import MatLike


class Camera:
    MAX_FAILURES = 20      # consecutive failed reads before giving up

    def __init__(self, index: int, width: int = 1280, height: int = 720) -> None:
        self.capture = cv2.VideoCapture(index)
        if not self.capture.isOpened():
            raise RuntimeError(f"Cannot open webcam {index}")

        # what we ask for
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, 30)

        # what the webcam actually gave us
        self.width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.failures = 0

    # None on a failed read, raises once they pile up. flip mirrors the frame:
    # true when the camera faces you
    def read(self, flip: bool) -> MatLike | None:
        ret, frame = self.capture.read()
        if not ret:
            self.failures += 1
            if self.failures > self.MAX_FAILURES:
                raise RuntimeError("Too many consecutive webcam read failures")
            return None

        self.failures = 0
        if flip:
            self._flip(frame)
        return frame

    def _flip(self, frame: MatLike) -> MatLike:
        return cv2.flip(frame, 1, frame)

    def close(self) -> None:
        self.capture.release()
