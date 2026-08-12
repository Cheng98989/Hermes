"""mediapipe wrapper: a frame in, 21 landmarks per hand out."""

from pathlib import Path

import cv2
import mediapipe as mp
from cv2.typing import MatLike
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import RunningMode

from mediapipe.tasks.python.vision.hand_landmarker import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
)

# built from this file, not from the working directory
MODEL_PATH = Path(__file__).parent.parent / "models" / "hand_landmarker.task"


class Hand:
    def __init__(self, number_of_hands: int = 1) -> None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model not found: {MODEL_PATH}")

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=RunningMode.VIDEO,
            num_hands=number_of_hands,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def get_all_landmarks(self, frame: MatLike, now: float) -> HandLandmarkerResult:
        return self.landmarker.detect_for_video(self._prepare_frame(frame), int(now * 1000))

    def _prepare_frame(self, frame: MatLike) -> mp.Image:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    def close(self) -> None:
        self.landmarker.close()


