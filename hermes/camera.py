import cv2
from cv2.typing import MatLike


class Camera:
    """Manages a webcam"""

    MAX_FAILURES = 20      # consecutive failed reads before giving up

    def __init__(self, index: int = 0, width: int = 1280, height: int = 720) -> None:
        self.capture = cv2.VideoCapture(index)
        if not self.capture.isOpened():
            raise RuntimeError(f"Cannot open webcam {index}")

        # width/height without self: these are the parameters, what we ASK for
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, 30)

        # self.width/self.height: what the webcam actually GAVE us.
        # get() returns a float (640.0), int() because we need whole pixels.
        self.width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.failures = 0

    def read(self) -> MatLike | None:
        ret, frame = self.capture.read()
        if not ret:
            self.failures += 1
            if self.failures > self.MAX_FAILURES:
                raise RuntimeError("Too many consecutive webcam read failures")
            return None
        self.failures = 0
        cv2.flip(frame, 1, frame)
        return frame

    def close(self) -> None:
        self.capture.release()
