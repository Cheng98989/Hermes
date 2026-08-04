import cv2
from hermes.camera import Camera
from hermes.hand import Hand
from hermes.overlay import Overlay
from hermes.fps import FpsCounter
from hermes.gestures import fingers_up, gesture_name

cam = Camera()
hand = Hand(number_of_hands=1)
fps_counter = FpsCounter()
overlay = Overlay(cam.width, cam.height)

while True:
    # Get the current FPS
    fps = fps_counter.tick()

    # Read a frame from the camera
    frame = cam.read()
    if frame is None:
        continue

    # Draw landmarks and FPS on the frame
    landmarks = hand.get_all_landmarks(frame)
    overlay.draw_landmarks(frame, landmarks)
    overlay.draw_fps(frame, fps)
    for single_hand in landmarks.hand_landmarks:
        up = fingers_up(single_hand)
        overlay.draw_text(frame, f"{len(up)}  {sorted(up)}", y=70)
        overlay.draw_text(frame, gesture_name(single_hand), y=100)

    # Display the frame
    cv2.imshow("Hermes", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.close()
hand.close()
cv2.destroyAllWindows()