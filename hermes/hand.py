"""mediapipe wrapper: a frame in, 21 landmarks per hand out."""

import sys
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

# Where the bundled files live, never the working directory. PyInstaller
# unpacks them beside the executable and points sys._MEIPASS at that folder;
# running from source there is no such attribute, so walk up from this file.
BUNDLE = getattr(sys, "_MEIPASS", None)
ROOT = Path(BUNDLE) if BUNDLE else Path(__file__).parent.parent

MODEL_PATH = ROOT / "models" / "hand_landmarker.task"


class Hand:
    def __init__(
        self,
        minimum_hand_detection_confidence: float,
        minimum_hand_presence_confidence: float,
        minimum_tracking_confidence: float,
        number_of_hands: int = 2,
    ) -> None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"Model not found: {MODEL_PATH}")

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=RunningMode.VIDEO,
            num_hands=number_of_hands,
            min_hand_detection_confidence=minimum_hand_detection_confidence,
            min_hand_presence_confidence=minimum_hand_presence_confidence,
            min_tracking_confidence=minimum_tracking_confidence,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def get_all_landmarks(self, frame: MatLike, now: float) -> HandLandmarkerResult:
        return self.landmarker.detect_for_video(self._prepare_frame(frame), int(now * 1000))

    def _prepare_frame(self, frame: MatLike) -> mp.Image:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    def close(self) -> None:
        self.landmarker.close()


