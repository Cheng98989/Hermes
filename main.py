import argparse
import time

import cv2
from hermes.camera import Camera
from hermes.hand import Hand
from hermes.overlay import Overlay
from hermes.fps import FpsCounter
from hermes.gestures import gesture_from_hands
from hermes.state import StateMachine, ACTIVE
from hermes.timing import GestureHold, Smoothed, SmoothedLandmarks
from hermes.killswitch import KillSwitch
from hermes.actions import Actions


parser = argparse.ArgumentParser(description="Control the desktop with hand gestures")
parser.add_argument(
    "--raw-landmarks",
    action="store_true",
    help="draw the skeleton as mediapipe reports it, without smoothing",
)
args = parser.parse_args()

cam = Camera()
hand = Hand(number_of_hands=1)
now = time.perf_counter()
fps_counter = FpsCounter(now, 60)
overlay = Overlay(cam.width, cam.height)
gesture_hold = GestureHold()
landmark_smoother = SmoothedLandmarks(window=5)     # world landmarks, for recognition
drawing_smoother = SmoothedLandmarks(window=5)      # normalised ones, for the preview
gesture_smoother = Smoothed(window=3)
state_machine = StateMachine()

kill_switch = KillSwitch()
actions = Actions()
last_command = ""
while True:
    now = time.perf_counter()

    # Get the current FPS
    fps = fps_counter.tick(now)

    # Read a frame from the camera
    frame = cam.read()
    if frame is None:
        continue

    # Draw landmarks and FPS on the frame
    landmarks = hand.get_all_landmarks(frame, now)
    # the preview is cosmetic: --raw-landmarks shows what mediapipe actually
    # reported, which is the honest view when something looks wrong
    if args.raw_landmarks:
        overlay.draw_landmarks(frame, landmarks.hand_landmarks)
    else:
        overlay.draw_landmarks(frame, drawing_smoother.update(landmarks.hand_landmarks))
    overlay.draw_fps(frame, fps)

    # Recognition runs on the world landmarks (real 3D, in metres); drawing
    # uses the normalised ones above, because those are what map to pixels.
    # Smoothing comes first, so every measurement downstream sees steady
    # numbers instead of mediapipe's frame-to-frame guesses.
    hands = landmark_smoother.update(landmarks.hand_world_landmarks)
    gesture = gesture_smoother.update(gesture_from_hands(hands))
    held = gesture_hold.update(gesture, now)
    state = state_machine.update(gesture, held)

    fired = actions.update(gesture, held, now, state == ACTIVE)
    if fired:
        last_command = fired
    overlay.draw_text(frame, f"{state}  {gesture}  {held:.1f}s | {last_command}", y=100)
    overlay.draw_state_border(frame, state)

    # Display the frame
    cv2.imshow("Hermes", frame)

    if kill_switch.triggered:
        break
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.close()
hand.close()
cv2.destroyAllWindows()
kill_switch.stop()