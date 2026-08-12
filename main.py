"""The loop. The only place that knows the whole chain."""

import argparse
import time
import threading

import cv2
from cv2.typing import MatLike

from hermes.actions import Actions
from hermes.anchors import finger_point, palm_point
from hermes.camera import Camera
from hermes.cursor import ZONE_MAX, ZONE_MIN, Cursor, screen_size, to_screen
from hermes.fps import FpsCounter
from hermes.hand import Hand
from hermes.hand_selector import HandSelector, RIGHT
from hermes.killswitch import KillSwitch
from hermes.landmarks import FrameHands, WorldHands
from hermes.overlay import Overlay
from hermes.recognition import finger_gap, gesture_from_hands, pinch_distance, pinch_guard_ok
from hermes.scroll import ScrollRate
from hermes.signals import DeadZone, Hold, OneEuroLandmarks
from hermes.state import ACTIVE, CURSOR, SCROLL, DragTracker, JoinedFingers, StateMachine

parser = argparse.ArgumentParser(description="Control the desktop with hand gestures")
parser.add_argument(
    "--raw-landmarks",
    action="store_true",
    help="draw the skeleton as mediapipe reports it, without smoothing",
)
args = parser.parse_args()

# --- hardware ---------------------------------------------------------------

cam = Camera()
hand = Hand(number_of_hands=2)
cursor = Cursor(*screen_size())
actions = Actions()
kill_switch = KillSwitch()
overlay = Overlay(cam.width, cam.height)

# --- recognition ------------------------------------------------------------

hand_selector = HandSelector(RIGHT)
one_euro_smoother = OneEuroLandmarks(min_cutoff=0.25, beta=10.0)          # normalised
one_euro_smoother_world = OneEuroLandmarks(min_cutoff=0.25, beta=10.0)  # world
joined_fingers = JoinedFingers(on_below=0.20, off_above=0.30)
gesture_hold = Hold()
state_machine = StateMachine()

# --- controls ---------------------------------------------------------------

dead_zone = DeadZone(radius=5.0)
drag_tracker = DragTracker(on_below=0.20, off_above=0.30, dwell=0.0)
scroll_rate = ScrollRate()

now = time.perf_counter()
fps_counter = FpsCounter(now, 60)


# what the two threads pass between them
class Shared:
    def __init__(self) -> None:
        self.running = True
        self.last_command = ""
        self.frame: MatLike | None = None


shared = Shared()


def process_frame() -> None:
    now = time.perf_counter()
    fps = fps_counter.tick(now)

    # read a frame
    frame = cam.read()
    if frame is None:
        return

    # mediapipe finds the hands, the selector keeps the one we obey
    landmarks = hand.get_all_landmarks(frame, now)
    selected_2d, selected_world = hand_selector.select(landmarks)

    # smoothed before anything measures them
    hands2d = FrameHands(one_euro_smoother.update(selected_2d, now))
    hands = WorldHands(one_euro_smoother_world.update(selected_world, now))

    # name the pose
    gesture = gesture_from_hands(hands)
    gap = finger_gap(hands)
    # victory becomes victory_closed while the two fingers touch
    gesture = joined_fingers.update(gesture, gap)
    # pinch
    distance = pinch_distance(hands)
    guard = pinch_guard_ok(hands)
    drag_status = drag_tracker.update(distance, guard, now)

    # how long the gesture has been held
    held = gesture_hold.update(gesture, now)
    # which mode that puts us in
    state = state_machine.update(gesture, held)

    # cursor mode
    mouse_position = palm_point(hands2d)
    if state == CURSOR and mouse_position is not None:
        # mapped here rather than inside Cursor, so the dead zone can sit in
        # between: a radius in pixels is the same on both axes
        target = to_screen(mouse_position, *cursor.screen_size)
        cursor.move_to_pixels(dead_zone.update(target))
    else:
        dead_zone.reset()
    cursor.set_pressed(drag_status and state == CURSOR)

    # scroll mode
    scroll_position = finger_point(hands2d)
    if state == SCROLL and scroll_position is not None:
        cursor.scroll(scroll_rate.update(scroll_position.y, now))
    else:
        scroll_rate.reset()

    # media keys
    fired = actions.update(gesture, held, now, state == ACTIVE)
    if fired:
        shared.last_command = fired

    # preview
    # --raw-landmarks draws what mediapipe reported, unsmoothed
    overlay.draw_landmarks(frame, selected_2d if args.raw_landmarks else hands2d)
    overlay.draw_fps(frame, fps)
    overlay.draw_mouse_mapping_area(frame, ZONE_MIN, ZONE_MAX)
    overlay.draw_scroll_origin(frame, scroll_rate.origin, scroll_rate.dead_zone)
    overlay.draw_text(
        frame,
        f"{state}  {gesture}  {held:.1f}s | {shared.last_command} | pinch {distance:.2f} | "
        f"drag {drag_status} | guard {guard}",
        y=100,
    )
    overlay.draw_text(frame, f"gap {gap:.2f}", y=130)
    overlay.draw_state_border(frame, state)
    shared.frame = frame


def work() -> None:
    try:
        while shared.running:
            process_frame()
    finally:
        shared.running = False
        cursor.set_pressed(False)


thread = threading.Thread(target=work, daemon=True)
thread.start()


# stops the worker and waits for it; False if it did not stop in time
def stop_work(max_time: float) -> bool:
    shared.running = False
    thread.join(timeout=max_time)
    return not thread.is_alive()


# the main thread only shows what the worker has already finished
while True:
    if shared.frame is not None:
        cv2.imshow("Hermes", shared.frame)

    quit_key = cv2.waitKey(50) & 0xFF == ord("q")
    if quit_key or kill_switch.triggered or not shared.running:
        break

stopped = stop_work(0.5)

# closing these while the worker is still inside cam.read() or mediapipe is
# what crashes; if it never stopped, leave them to the operating system
if stopped:
    cam.close()
    hand.close()

cv2.destroyAllWindows()
kill_switch.stop()