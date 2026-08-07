# Hermes

Control the desktop with hand gestures seen through a webcam.

**Status: work in progress.** Hermes sends media keys - volume up, volume
down, play/pause - and moves the mouse pointer, with click and drag by
pinching thumb and index together.

`ROADMAP.md` has what is left to do. `ARCHITECTURE.md` explains how it works,
why it is built this way, and which approaches were tried and measured before
being rejected.

---

## Requirements

- Python 3.11
- a webcam
- Windows 11 (what it is developed and tested on)

Linux should work for the vision part. Sending keystrokes will work under X11
but **not** under Wayland, which blocks synthetic input by design.

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

A window opens with the webcam feed. Press **`q`** with that window focused to
quit, or **`Esc`** from anywhere: `Esc` is watched by a global listener, so it
still stops Hermes when the preview is behind another window.

### Options

```
--raw-landmarks    draw the skeleton as mediapipe reports it, without smoothing
```

That flag changes the preview only, never recognition: it shows the raw
positions, which is the honest view when something looks wrong on screen.

### What is on screen

```
FPS: 30.5                       frames per second (green, top)
ACTIVE  victory  1.2s | point   state, gesture, how long it has been held,
                                and the last command that fired
```

The 21 hand landmarks are drawn as green dots joined by white lines, and the
frame gets a border coloured by state: red for `IDLE`, green for `ACTIVE`.

---

## The three modes

Hermes starts in `IDLE` and ignores everything except the gesture that wakes
it. Media commands fire only in `ACTIVE`; the pointer moves only in `CURSOR`.

| From | Gesture | Held for | To |
|---|---|---|---|
| `IDLE` | open palm | 1 s | `ACTIVE` |
| `ACTIVE` | fist | 1 s | `IDLE` |
| `ACTIVE` | point | 0.5 s | `CURSOR` |
| `CURSOR` | open palm | 0.5 s | `ACTIVE` |
| `ACTIVE` or `CURSOR` | no hand in frame | 3 s | `IDLE` |

The last row is the safety timeout: forgetting to switch Hermes off is the
dangerous mistake and you do not notice it, while switching off too early is
merely annoying - so it fails towards off. It works because "no hand at all"
is treated as a gesture of its own (`none`), distinct from `unknown`.

There is deliberately **no** way to leave `CURSOR` with a fist: while
pinching, the fingers read as one, so that rule would end cursor mode in the
middle of a drag.

Those rules are the whole of `TRANSITIONS` in `hermes/state.py`.

---

## Moving the pointer

In `CURSOR` the pointer follows the base knuckle of the middle finger - not a
fingertip, because fingertips move when you pinch and a click must not drag
the pointer with it.

Only the **middle 40% of the camera view** maps to the whole screen. The
corners are neither comfortable to reach nor well tracked, and pushing the
hand that far takes the fingers out of frame, which loses the pinch. A green
rectangle in the preview shows the active area; outside it the pointer sticks
to the screen edge.

**Pinch thumb and index together to hold the left button.** Pinch and release
for a click; pinch, move and release to drag. The other three fingers must be
closed for a pinch to register - that is the shape a hand already has while
pointing, and it rejects the half-open poses a hand passes through on its way
somewhere else.

The pointer covers the primary monitor only.

---

## Gestures

| Gesture | Extended fingers |
|---|---|
| `fist` | none |
| `point` | index |
| `victory` | index, middle |
| `three` | index, middle, ring |
| `rock` | index, pinky |
| `rock_with_ring` | index, ring, pinky |
| `middle_ring_pinky` | middle, ring, pinky |
| `open_palm` | index, middle, ring, pinky |

Anything else reads `unknown`, and no hand in frame reads `none`.

The thumb takes no part in recognition. It folds sideways instead of curling,
and in a natural fist it rests outside the other fingers - far enough out to
pass any "is it extended?" test tried here, which made a plain fist register
as something else. A fist is what switches Hermes off, so four fingers that
are always right beat five with one that lies.

To add a gesture, add one line to `GESTURES` in `hermes/gestures.py`. No logic
to touch, and its test is generated automatically from the table.

### What is measured

Recognition runs on mediapipe's **world landmarks**: real 3D positions in
metres, centred on the hand, not the normalised image coordinates the preview
is drawn from. Image coordinates are a shadow - they change when the hand
merely turns - while world coordinates describe the hand itself. A finger
counts as extended when its tip is farther from the wrist than its middle
knuckle, in three dimensions.

Before anything measures them, landmark positions are averaged over the last
few frames. Smoothing the numbers comes first, so every measurement downstream
sees steady values instead of mediapipe's frame-to-frame guesses; once a value
has been compared against a threshold, the noise has already turned into two
opposite answers and no amount of voting recovers it.

---

## Commands

Only in `ACTIVE`.

| Gesture | Key sent | Fires after | Then |
|---|---|---|---|
| `victory` | volume up | 0.5 s | repeats every 0.3 s while held |
| `middle_ring_pinky` | volume down | 0.5 s | repeats every 0.3 s while held |
| `rock` | play / pause | 0.5 s | once per hold |

The dwell exists because the loop runs at 30 fps: a gesture held for a second
is thirty frames, and without it that would be thirty keystrokes. Volume
repeats because one press moves it 2%; play/pause fires once, because firing
it twice puts you back where you started.

`open_palm`, `fist` and `point` are deliberately bound to nothing - they
change state, and the dwell here is shorter than the one the state machine
uses, so a command bound to any of them would fire at the very moment of
switching.

The table is `ACTIONS` in `hermes/actions.py`.

---

## Tests

```
.venv\Scripts\python -m pytest
```

Use `python -m pytest`, not bare `pytest`: without `python -m` the project
root is not on the import path and `import hermes` fails.

The tested modules are the pure ones - `gestures.py`, `state.py` and
`filters.py` - because they are the ones with no I/O: no webcam, no mediapipe,
and no clock, since the current instant is passed in rather than read. Run the
suite after every change to those files.

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
  filters.py         noisy stream -> steady answer: Hold, Repeater,
                     Hysteresis, OneEuroFilter, DeadZone  [pure]
  state.py           IDLE / ACTIVE / CURSOR, and the pinch phases  [pure]
  actions.py         gesture -> media key, sent with pynput
  cursor.py          a point in the frame -> the mouse pointer and its button
  killswitch.py      global Esc listener that stops the app
  overlay.py         drawing on the frame
  fps.py             sliding-window fps counter
models/              the mediapipe hand landmark model
tests/
  test_gestures.py   fingers, gesture names
  test_state.py      the state machine
  test_filters.py    holds, repeats and smoothing
  test_pointer.py    the palm anchor, the dead zone and the jitter meter
ARCHITECTURE.md      how it works, why, and what was rejected
ROADMAP.md           milestones and what is left
```

The modules marked pure import nothing but the standard library: data in, data
out. That is what makes them testable without hardware. The clock counts as
I/O for this purpose - `main.py` reads `perf_counter()` once per frame and
hands the same instant to everyone, so a test can say "held for 1.1 seconds"
by passing the number 1.1 instead of waiting.

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
correcting mistakes and rewriting passages along the way. The files under
`tests/` are the ones generated outright, and say so in their headers.

The findings recorded in `ROADMAP.md` - the webcam being the bottleneck, the
thumb rotating around a pivot next to the wrist, `palm_size` collapsing under
foreshortening - came from measurements taken on this machine.
