from pathlib import Path

import cv2
import mediapipe as mp
from cv2.typing import MatLike
from mediapipe.tasks.python.core.base_options import BaseOptions
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

# Built from this file's own location, NOT from the current working directory:
# a relative path would break as soon as the app is launched from elsewhere.
# hand.py -> hermes/ -> project root -> models/
MODEL_PATH = Path(__file__).parent.parent / "models" / "hand_landmarker.task"


class Hand:
    def __init__(self, number_of_hands: int = 1) -> None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model not found: {MODEL_PATH}")

        options = HandLandmarkerOptions(
            # str(): mediapipe's C++ layer cannot take a Path object. It accepts
            # it here without complaining and then fails later while loading.
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=RunningMode.VIDEO,
            num_hands=number_of_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def get_all_landmarks(self, frame: MatLike, now: float) -> HandLandmarkerResult:
        mp_image = self._prepare_frame(frame)
        timestamp_ms = int(now * 1000)
        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def _prepare_frame(self, frame: MatLike) -> mp.Image:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return mp_image

    def close(self) -> None:
        self.landmarker.close()
