# Hermes

Control the desktop with hand gestures seen through a webcam.

**Status: work in progress.** Hermes currently recognises hand gestures and
shows them on screen. It does not control anything yet - mouse and keyboard
come later (see `ROADMAP.md`).

---

## Requirements

- Python 3.11
- a webcam
- Windows 11 (what it is developed and tested on)

Linux should work for the vision part. Controlling mouse and keyboard will
work under X11 but **not** under Wayland, which blocks synthetic input by
design.

---

## Install

From the project root:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

The hand landmark model is already in `models/`, nothing else to download.

---

## Run

```
.venv\Scripts\python main.py
```

Always launch from the project root, so `import hermes` resolves.

A window opens with the webcam feed. Press **`q`** to quit.

### What is on screen

```
FPS: 30.5                     frames per second (green, top)
2  ['index', 'middle']        how many fingers are up, and which
victory                       the recognised gesture
```

The 21 hand landmarks are drawn as green dots joined by white lines.

---

## Gestures

| Gesture | Extended fingers |
|---|---|
| `fist` | none |
| `point` | index |
| `victory` | index, middle |
| `thumb_up` | thumb |
| `gun` | thumb, index |
| `rock` | index, pinky |
| `spiderman` | thumb, index, pinky |
| `open_palm` | all five |

Anything else reads `unknown`.

To add a gesture, add one line to `GESTURES` in `hermes/gestures.py`. No
logic to touch, and its test is generated automatically.

---

## Tests

```
.venv\Scripts\python -m pytest
```

Use `python -m pytest`, not bare `pytest`: without `python -m` the project
root is not on the import path and `import hermes` fails.

Only `hermes/gestures.py` is tested, because it is the only module with no
I/O - no webcam and no mediapipe needed to run its tests. Run them after
every change to that file.

Useful flags: `-q` compact, `-v` one line per test, `-k word` to run only
matching tests.

---

## Project layout

```
main.py              the loop that wires everything together
hermes/
  camera.py          webcam: open, read, mirror flip, close
  hand.py            mediapipe wrapper: frame -> 21 landmarks
  gestures.py        landmarks -> extended fingers -> gesture name  [pure]
  overlay.py         drawing on the frame
  fps.py             sliding-window fps counter
models/              the mediapipe hand landmark model
tests/               pytest suite for gestures.py
ROADMAP.md           milestones, decisions and measurements
```

`gestures.py` is marked pure because it imports nothing but `math`: data in,
data out. That is what makes it testable without hardware.

---

## Known limitations

- **Light matters.** In a dark room lit only by the monitor, recognition
  degrades badly: the webcam lengthens its exposure, the hand blurs, and
  skin tone information is lost.
- **Webcam settings matter.** Saturation or white balance left in an odd
  state (from any other app - the driver keeps them) can break detection
  entirely. Reset them under Windows Settings > Bluetooth & devices > Cameras.
- **Frame rate is capped by the webcam**, not by the code: measured 30 fps at
  640x480, of which only ~13 ms per frame is actual work. See `ROADMAP.md`.
- One hand at a time by default (`Hand(number_of_hands=...)` to change it).

---

## How this was built

A school project, written to be understood rather than to be finished fast.

Design and code were worked out with Claude (Anthropic) acting as a tutor:
the reasoning was done in conversation, the code typed by hand, with Claude
correcting mistakes and rewriting passages along the way.
`tests/test_gestures.py` is the one file generated outright, and says so in
its header.

The findings recorded in `ROADMAP.md` - the webcam being the bottleneck, the
thumb rotating around a pivot next to the wrist, `palm_size` collapsing under
foreshortening - came from measurements taken on this machine.
