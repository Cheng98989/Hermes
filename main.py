import cv2
import time
from hermes.camera import Camera
from hermes.hand import Hand
from hermes.overlay import Overlay
from hermes.fps import FpsCounter
from hermes.gestures import gesture_from_hands
from hermes.state import GestureHold, StateMachine, EdgeTrigger, ACTIVE
from hermes.killswitch import KillSwitch
from hermes.actions import Actions, COMMAND_DWELL

cam = Camera()
hand = Hand(number_of_hands=1)
now = time.perf_counter()
fps_counter = FpsCounter(now, 60)
overlay = Overlay(cam.width, cam.height)
gesture_hold = GestureHold()
state_machine = StateMachine()
edge_trigger = EdgeTrigger()
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
    overlay.draw_landmarks(frame, landmarks)
    overlay.draw_fps(frame, fps)

    gesture = gesture_from_hands(landmarks.hand_landmarks)
    held = gesture_hold.update(gesture, now)
    state = state_machine.update(gesture, held)

    # Actions
    is_command = state == ACTIVE and held >= COMMAND_DWELL

    if edge_trigger.rising(is_command):
        if actions.run(gesture):
            last_command = gesture


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