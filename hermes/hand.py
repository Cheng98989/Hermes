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

LEFT = "Left"
RIGHT = "Right"

OPPOSITE = {LEFT: RIGHT, RIGHT: LEFT}


class HandSelector:
    """Keeps only the hand Hermes is configured to obey.

    mediapipe is asked for two hands so it can *see* the other one; this is
    what stops the other one from being acted on. Without it the recogniser
    reads whichever hand mediapipe happened to list first, so a hand resting
    on the desk can fire a command.

    On the label: camera.py mirrors every frame before mediapipe sees it, and
    *measured* the labels then come back the wrong way round - a real right
    hand is reported as "Left". So the label looked for here is the opposite
    of the hand asked for, which is what labels_mirrored says.

    The two are tied together. Taking the flip out of camera.py means passing
    labels_mirrored=False. Flipping after detection instead is not an option:
    the normalised x coordinates drive the cursor, and un-mirroring those
    would send the pointer the wrong way.
    """

    def __init__(
        self,
        selected_hand: str,
        min_score: float = 0.9,
        labels_mirrored: bool = True,
    ) -> None:
        if selected_hand not in (LEFT, RIGHT):
            raise ValueError("selected_hand must be Left or Right")

        self.selected_hand = selected_hand
        self.min_score = min_score
        # what mediapipe will actually call the hand we want
        self.label = OPPOSITE[selected_hand] if labels_mirrored else selected_hand

    def select_index(self, result: HandLandmarkerResult) -> int | None:
        """Index of the configured hand, or None when it is not in frame.

        Takes the best-scoring match rather than the first: when mediapipe is
        unsure it can label both hands the same way, and the one it lists
        first is not the one it believes in.
        """
        best_index = None
        best_score = self.min_score

        for index, handedness in enumerate(result.handedness):
            category = handedness[0]
            if category.category_name == self.label and category.score >= best_score:
                best_index = index
                best_score = category.score

        return best_index

    def select(self, result: HandLandmarkerResult) -> tuple[list, list]:
        """The (normalised, world) landmarks of the chosen hand.

        Both come back in mediapipe's own shape - a list of hands - so the
        rest of the app keeps reading hands[0] and needs no special case.

        Empty lists when the chosen hand is absent, which every reader
        downstream already treats as "no hand in frame": the gesture becomes
        "none", the pinch distance infinity, and the smoothers drop their
        history. Returning the result unfiltered instead would let the other
        hand drive the app, which is the whole thing this class exists to
        prevent.
        """
        index = self.select_index(result)
        if index is None:
            return [], []

        return [result.hand_landmarks[index]], [result.hand_world_landmarks[index]]