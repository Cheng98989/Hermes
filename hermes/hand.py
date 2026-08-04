import time

import cv2
import mediapipe as mp
from cv2.typing import MatLike
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarksConnections, RunningMode

# imported from their defining module, not from the vision package: the package
# only re-exports them as aliases, and Pylance cannot resolve an alias to a type
from mediapipe.tasks.python.vision.hand_landmarker import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
)

# mediapipe's Connection objects turned into plain (start, end) index pairs,
# so the rest of the app never has to import mediapipe just to draw a hand.
# Module level: the anatomy of a hand never changes, so this is built once at
# import time and shared by everyone.
CONNECTIONS: list[tuple[int, int]] = []
for c in HandLandmarksConnections.HAND_CONNECTIONS:
    CONNECTIONS.append((c.start, c.end))

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="models/hand_landmarker.task"),
    running_mode=RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
)

landmarker = HandLandmarker.create_from_options(options)


class Hand:
    def __init__(self, frame: MatLike) -> None:
        self.frame = frame

    def get_all_landmarks(self) -> HandLandmarkerResult:
        mp_image = self._prepare_frame()
        timestamp_ms = int(time.perf_counter() * 1000)
        return landmarker.detect_for_video(mp_image, timestamp_ms)

    def _prepare_frame(self) -> mp.Image:
        rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return mp_image
