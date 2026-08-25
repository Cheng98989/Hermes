"""Selects the one hand Iris obeys."""

from mediapipe.tasks.python.vision.hand_landmarker import HandLandmarkerResult

from iris.landmarks import FrameHands, WorldHands

LEFT = "Left"
RIGHT = "Right"

OPPOSITE = {LEFT: RIGHT, RIGHT: LEFT}


# Keeps only the hand Iris is configured to obey; mediapipe is asked for two
# so it can see the other one.
#
# camera.py mirrors the frame by default, which flips the labels: pass
# labels_mirrored=False if that flip is turned off
class HandSelector:
    def __init__(self, selected_hand: str, labels_mirrored: bool, min_score: float = 0.5) -> None:
        if selected_hand not in (LEFT, RIGHT):
            raise ValueError("selected_hand must be Left or Right")

        self.selected_hand = selected_hand                    # what the user wants
        self.min_score = min_score
        self.label = OPPOSITE[selected_hand] if labels_mirrored else selected_hand

    # the best-scoring match, not the first: when mediapipe is unsure it can
    # label both hands the same way
    def select_index(self, result: HandLandmarkerResult) -> int | None:
        best_index = None
        best_score = self.min_score

        for index, handedness in enumerate(result.handedness):
            category = handedness[0]
            if category.category_name == self.label and category.score >= best_score:
                best_index = index
                best_score = category.score

        return best_index

    # the normalised and world landmarks of the chosen hand
    def select(self, result: HandLandmarkerResult) -> tuple[FrameHands, WorldHands]:
        index = self.select_index(result)
        if index is None:
            return FrameHands([]), WorldHands([])

        return (
            FrameHands([result.hand_landmarks[index]]),
            WorldHands([result.hand_world_landmarks[index]]),
        )
