import argparse
import time

import cv2
from hermes.camera import Camera
from hermes.hand import Hand, HandSelector, RIGHT
from hermes.overlay import Overlay
from hermes.fps import FpsCounter
from hermes.gestures import gesture_from_hands, palm_point, pinch_distance, pinch_guard_ok
from hermes.state import StateMachine, ACTIVE, CURSOR, DragTracker
from hermes.filters import DeadZone, Hold, OneEuroLandmarks, Wander
from hermes.killswitch import KillSwitch
from hermes.actions import Actions
from hermes.cursor import Cursor, screen_size, to_screen

parser = argparse.ArgumentParser(description="Control the desktop with hand gestures")
parser.add_argument(
    "--raw-landmarks",
    action="store_true",
    help="draw the skeleton as mediapipe reports it, without smoothing",
)
args = parser.parse_args()

cam = Camera()
hand = Hand(number_of_hands=2)
hand_selector = HandSelector(RIGHT)
now = time.perf_counter()
fps_counter = FpsCounter(now, 60)
overlay = Overlay(cam.width, cam.height)
gesture_hold = Hold()
# The pointer chain, in the order the numbers travel along it. Every one of
# these is a dial: turn one at a time and watch "jit" on the overlay, because
# turning two at once tells you nothing about either.
#
#   palm_point  ->  one_euro_smoother  ->  to_screen  ->  dead_zone  ->  mouse
#
# beta is in the units of the signal, so the two One Euro instances below are
# not interchangeable: the first is fed fractions of the frame, the second
# metres.
one_euro_smoother = OneEuroLandmarks(min_cutoff=0.4, beta=4.0)         # normalised, drives the cursor
one_euro_smoother_world = OneEuroLandmarks(min_cutoff=0.25, beta=10.0)   # world, drives recognition
dead_zone = DeadZone(radius=5.0)     # screen pixels
wander = Wander(window=60)           # two seconds at 30 fps; tuning only
state_machine = StateMachine()

drag_tracker = DragTracker(on_below=0.20, off_above=0.30, dwell=0.0)
kill_switch = KillSwitch()
actions = Actions()
cursor = Cursor(*screen_size())
last_command = ""
step = spread = 0.0      # how still the pointer is, in pixels; see Wander

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

    selected_2d, selected_world = hand_selector.select(landmarks)

    # Recognition runs on the world landmarks (real 3D, in metres); the
    # preview and the cursor use the normalised ones, because those are what
    # map to pixels. Smoothing comes first either way, so every measurement
    # downstream sees steady numbers instead of frame-to-frame guesses.
    hands2d = one_euro_smoother.update(selected_2d, now)
    hands = one_euro_smoother_world.update(selected_world, now)

    # the preview is cosmetic: --raw-landmarks shows what mediapipe actually
    # reported, which is the honest view when something looks wrong
    if args.raw_landmarks:
        overlay.draw_landmarks(frame, selected_2d)
    else:
        overlay.draw_landmarks(frame, hands2d)

    overlay.draw_fps(frame, fps)
    overlay.draw_mouse_mapping_area(frame)

    gesture = gesture_from_hands(hands)

    distance = pinch_distance(hands)
    guard = pinch_guard_ok(hands)
    drag_status = drag_tracker.update(distance, guard, now)
    held = gesture_hold.update(gesture, now)
    state = state_machine.update(gesture, held)

    mouse_position = palm_point(hands2d)
    if state == CURSOR and mouse_position is not None:
        # the mapping happens here rather than inside Cursor.move_to, so the
        # dead zone can work in pixels: a radius in pixels is the same on both
        # axes, while the same radius in normalised units is not
        target = to_screen(*mouse_position, *cursor.screen_size)

        # measured BEFORE the dead zone on purpose - after it the reading at
        # rest is zero by construction, which says nothing about the filter
        step, spread = wander.update(*target)

        cursor.move_to_pixels(*dead_zone.update(*target))
    else:
        # the pointer is not being driven: drop the anchor, or the hand coming
        # back somewhere else would crawl there from where it was left
        dead_zone.reset()
        wander.reset()
        step = spread = 0.0

    cursor.set_pressed(drag_status and state == CURSOR)      # every frame, always

    fired = actions.update(gesture, held, now, state == ACTIVE)
    if fired:
        last_command = fired
    overlay.draw_text(frame, f"{state}  {gesture}  {held:.1f}s | {last_command} | {distance:.2f} | drag_status={drag_status} | guard: {guard}", y=100)
    # hold the hand still and read these: step is the per-frame shimmer, spread
    # the excursion over two seconds. Both in screen pixels, before the dead
    # zone. See "Tuning the pointer" in ARCHITECTURE.md.
    overlay.draw_text(frame, f"jit step {step:.1f}px  spread {spread:.1f}px  (zone {dead_zone.radius:.0f}px)", y=130)
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