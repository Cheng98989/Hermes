import cv2
from hermes.camera import Camera
from hermes.hand import Hand
from hermes.overlay import Overlay
from hermes.fps import FpsCounter

cam = Camera()
fps_counter = FpsCounter()
overlay = Overlay(cam.width, cam.height)
while True:
    # Get the current FPS
    fps = fps_counter.tick()

    # Read a frame from the camera
    frame = cam.read()
    if frame is None:
        continue

    # Process the frame to detect hands and get landmarks
    hand = Hand(frame)

    # Draw landmarks and FPS on the frame
    landmarks = hand.get_all_landmarks()
    if landmarks is not None:
        overlay.draw_landmarks(frame, landmarks)
        overlay.draw_fps(frame, fps)

    # Display the frame
    cv2.imshow("Hermes", frame)

    # Exit the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cam.close()