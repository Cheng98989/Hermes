import cv2
import time

#mediapipe
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, HandLandmarksConnections, RunningMode

opzioni = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="modelli/hand_landmarker.task"),
    running_mode=RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.3,
    min_tracking_confidence=0.3,
)

landmarker = HandLandmarker.create_from_options(opzioni)

#end import mediapipe as mp




capture_width = 640
capture_height = 480

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, capture_width)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_height)
capture.set(cv2.CAP_PROP_FPS, 30)
count = 0
fps = 0

tempo_lettura = 0.0          # ← i tre accumulatori
tempo_elaborazione = 0.0
tempo_display = 0.0
start_time = time.perf_counter()
while True:
    #fps calculation
    if count == 30:
        end_time = time.perf_counter()
        fps = count / (end_time - start_time)
         # da secondi totali a millisecondi medi per frame:
        #   / count  → media su un frame      * 1000 → millisecondi
        print(f"FPS: {fps:.1f} | "
              f"lettura {tempo_lettura / count * 1000:.1f} ms | "
              f"elab {tempo_elaborazione / count * 1000:.1f} ms | "
              f"display {tempo_display / count * 1000:.1f} ms")
        count = 0
        tempo_lettura = 0.0       # ← azzeri anche questi, insieme a count
        tempo_elaborazione = 0.0
        tempo_display = 0.0
        start_time = time.perf_counter()

    #lettura frame
    t0 = time.perf_counter()

    ret, frame = capture.read()

    #elaborazione frame
    t1 = time.perf_counter()

    frame = cv2.flip(frame, 1)

    mediapipe_feed = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #metto il frame in una variabile di tipo immagine di mediapipe
    immagine_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=mediapipe_feed)
    timestamp_ms = int(time.perf_counter() * 1000)
    risultato = landmarker.detect_for_video(immagine_mp, timestamp_ms)
    for mano in risultato.hand_landmarks:
        for c in HandLandmarksConnections.HAND_CONNECTIONS:
            p1 = mano[c.start]        # ← dall'indice al punto
            p2 = mano[c.end]
            x1, y1 = int(p1.x * capture_width), int(p1.y * capture_height)
            x2, y2 = int(p2.x * capture_width), int(p2.y * capture_height)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        for punto in mano:
            x = int(punto.x * capture_width)
            y = int(punto.y * capture_height)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
    
    frame = cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    #display frame
    t2 = time.perf_counter()
    
    cv2.imshow('Video Capture', frame)
    tasto = cv2.waitKey(1)
    t3 = time.perf_counter()

    tempo_lettura += t1 - t0            # ← accumuli, non stampi
    tempo_elaborazione += t2 - t1
    tempo_display += t3 - t2
    count += 1  
    if tasto & 0xFF == ord('q'):
        break