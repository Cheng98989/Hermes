"""The webcam: open, read, mirror, close."""

import cv2
from cv2.typing import MatLike

CAMERA_NUMBER = 4


class Camera:
    MAX_FAILURES = 20      # consecutive failed reads before giving up

    def __init__(
        self,
        index: int,
        width: int = 1280,
        height: int = 720,
        check_range: int = CAMERA_NUMBER,
    ) -> None:
        self.lost = False
        self.capture = cv2.VideoCapture(index)
        if not self.capture.isOpened():
            for i in range(check_range):
                self.capture = cv2.VideoCapture(i)
                if self.capture.isOpened():
                    index = i
                    break
        if not self.capture.isOpened():
            self.lost = True
        self.camera_index = index
        # what we ask for
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, 30)

        w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # what the webcam actually gave us
        self.width = w if w > 0 else width
        self.height = h if h > 0 else height

        self.failures = 0

    # None on a failed read, raises once they pile up. flip mirrors the frame:
    # true when the camera faces you
    def read(self, flip: bool) -> MatLike | None:
        ret, frame = self.capture.read()
        if not ret:
            self.failures += 1
            if self.failures > self.MAX_FAILURES:
                self.lost = True
            return None

        self.failures = 0
        if flip:
            self._flip(frame)
        return frame

    def _flip(self, frame: MatLike) -> MatLike:
        return cv2.flip(frame, 1, frame)

    def close(self) -> None:
        self.capture.release()


def get_available_camera(check_range: int = CAMERA_NUMBER) -> list[int]:
    indices: list[int] = []
    for i in range(check_range):
        camera = cv2.VideoCapture(i)
        if camera.isOpened():
            camera.release()
            indices.append(i)
    return indices
