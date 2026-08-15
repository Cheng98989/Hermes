"""The loop. The only place that knows the whole chain."""

import argparse
import time
import threading

from cv2.typing import MatLike

from hermes.actions import Actions
from hermes.anchors import finger_point, palm_point
from hermes.camera import Camera, get_available_camera
from hermes.cursor import Cursor, screen_size, to_screen
from hermes.fps import FpsCounter
from hermes.hand import Hand
from hermes.hand_selector import HandSelector
from hermes.killswitch import KillSwitch
from hermes.landmarks import FrameHands, WorldHands
from hermes.overlay import Overlay
from hermes.recognition import finger_gap, gesture_from_hands, pinch_distance, pinch_guard_ok
from hermes.scroll import ScrollRate
from hermes.signals import DeadZone, Hold, OneEuroLandmarks
from hermes.state import IDLE, ACTIVE, CURSOR, SCROLL, DragTracker, JoinedFingers, StateMachine
from hermes.config import ICON_PATH, load
from hermes.ui import Preview, Tray, Settings

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

parser = argparse.ArgumentParser(description="Control the desktop with hand gestures")
parser.add_argument(
    "--raw-landmarks",
    action="store_true",
    help="draw the skeleton as mediapipe reports it, without smoothing",
)
args = parser.parse_args()

config = load()

# --- Qt ---------------------------------------------------------------------


app = QApplication([])

# --- hardware ---------------------------------------------------------------

cam = Camera(config.camera_index)
if cam.lost:
    QMessageBox.warning(
        None,
        "No camera",
        "No webcam answered. Hermes will run without a picture; "
        "connect one and restart.",
    )
elif cam.camera_index != config.camera_index:
    QMessageBox.warning(
        None,
        "Camera unavailable",
        f"Camera {config.camera_index} did not answer. "
        f"Camera {cam.camera_index} is being used instead.",
    )

hand = Hand(
    config.min_hand_detection_confidence,
    config.min_hand_presence_confidence,
    config.min_tracking_confidence,
)

# --- UI ---------------------------------------------------------------------

app.setQuitOnLastWindowClosed(False)


cursor = Cursor(*screen_size())
mapping_fraction = (config.zone_min, config.zone_max)
actions = Actions()
kill_switch = KillSwitch()
overlay = Overlay(cam.width, cam.height, config.state_colors)

# --- recognition ------------------------------------------------------------

hand_selector = HandSelector(config.hand, labels_mirrored=config.camera_faces_you)
one_euro_smoother = OneEuroLandmarks(config.cursor_min_cutoff, config.cursor_beta)    # normalised
one_euro_smoother_world = OneEuroLandmarks(config.world_min_cutoff, config.world_beta)    # world
joined_fingers = JoinedFingers(on_below=config.fingers_joined, off_above=config.fingers_apart)
gesture_hold = Hold()
state_machine = StateMachine()    # TODO: make the transition dwells configurable too

# --- controls ---------------------------------------------------------------

dead_zone = DeadZone(radius=config.cursor_dead_zone_radius)
drag_tracker = DragTracker(config.pinch_close, config.pinch_open, config.pinch_dwell)
scroll_rate = ScrollRate(config.scroll_dead_zone, config.scroll_span, config.scroll_speed)

now = time.perf_counter()
fps_counter = FpsCounter(now, 60)


# what the two threads pass between them
class Shared:
    def __init__(self, now: float) -> None:
        self.running = True
        self.last_command = ""
        self.last_frame_time = now
        self.camera_lost = False
        self.frame: MatLike | None = None


shared = Shared(now)


def process_frame() -> None:
    now = time.perf_counter()
    shared.last_frame_time = now

    fps = fps_counter.tick(now)

    # read a frame
    frame = cam.read(config.camera_faces_you)
    if cam.lost:
        shared.camera_lost = True
        cursor.set_pressed(False)
        state_machine.set_state(IDLE)
        return
    if frame is None:
        return

    shared.camera_lost = False

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
        target = to_screen(mouse_position, *cursor.screen_size, *mapping_fraction)
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
    if config.show_skeleton:
        overlay.draw_landmarks(frame, selected_2d if args.raw_landmarks else hands2d)
    if config.show_mapping_area:
        overlay.draw_mouse_mapping_area(frame, *mapping_fraction)
    if config.show_debug_text:
        overlay.draw_fps(frame, fps)
        overlay.draw_text(
            frame,
            f"{state}  {gesture}  {held:.1f}s | {shared.last_command} | pinch {distance:.2f} | "
            f"drag {drag_status} | guard {guard}",
            y=100,
        )
        overlay.draw_text(frame, f"gap {gap:.2f}", y=130)
    overlay.draw_scroll_origin(frame, scroll_rate.origin, scroll_rate.dead_zone)
    overlay.draw_state_border(frame, state)
    shared.frame = frame


def work() -> None:
    try:
        while shared.running:
            process_frame()
    finally:
        shared.running = False


thread = threading.Thread(target=work, daemon=True)
thread.start()


# stops the worker and waits for it; False if it did not stop in time
def stop_work(max_time: float) -> bool:
    shared.running = False
    thread.join(timeout=max_time)
    return not thread.is_alive()


def check_quit() -> None:
    worker_stalled = time.perf_counter() - shared.last_frame_time > 2
    if kill_switch.triggered or not shared.running or worker_stalled:
        app.quit()

quit_checker = QTimer(app)
quit_checker.timeout.connect(check_quit)
quit_checker.start(100)

preview = Preview(shared, cam.width, cam.height)
settings = Settings(config, get_available_camera)
tray = Tray(ICON_PATH, preview, settings, app.quit)
tray.show()

if config.show_preview:
    preview.show()

app.exec()

stopped = stop_work(0.5)
cursor.set_pressed(False)
# closing these while the worker is still inside cam.read() or mediapipe is
# what crashes; if it never stopped, leave them to the operating system
if stopped:
    cam.close()
    hand.close()

kill_switch.stop()
