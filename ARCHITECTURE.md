# Hermes — how it works and why

Written to bring someone up to speed quickly: a new contributor, a fresh
chat, or the author in a month's time. `README.md` says how to run it,
`ROADMAP.md` says what is left. This file says **why the code looks the way
it does**, and — just as important — **what has already been tried and
rejected**, so nobody spends a day rediscovering it.

Everything below marked *measured* came from real measurements on the
author's machine: a Windows 11 laptop, a webcam that only exposes the
uncompressed YUY2 format, two monitors.

---

## What it is

An app that watches a hand through the webcam and turns gestures into
desktop commands: media keys, and a mouse pointer driven by hand position.

It exists because of a small desk. Studying with keyboard and mouse pushed
out of reach, small interactions with the computer — pause a video, change
the volume, move a window — meant rearranging the desk each time.

School project, Python 3, deadline 27 August 2026.

---

## The pipeline

Each frame goes through the same chain. `main.py` is the only place that
knows all of it.

```
webcam ─► mediapipe ─► smoothing ─► measurements ─► gesture name
                                                         │
                                          ┌──────────────┴──────────────┐
                                          ▼                             ▼
                                    state machine                  hold timers
                                          │                             │
                                          └──────────────┬──────────────┘
                                                         ▼
                                              media keys / mouse
```

Modules, and what each one is responsible for:

| Module | Job | Pure? |
|---|---|---|
| `camera.py` | open the webcam, read frames, mirror them, close | I/O |
| `hand.py` | mediapipe wrapper: frame → 21 landmarks | I/O |
| `filters.py` | noisy stream → steady answer | **pure** |
| `gestures.py` | landmarks → which fingers are up → gesture name | **pure** |
| `state.py` | IDLE / ACTIVE / CURSOR, and the pinch phases | **pure** |
| `actions.py` | gesture → media key, via pynput | I/O |
| `cursor.py` | normalised point → mouse position and button | I/O |
| `overlay.py` | draw on the preview frame | I/O |
| `killswitch.py` | global Esc listener | I/O |
| `fps.py` | frame rate over a sliding window | pure-ish |

**Pure** means: imports nothing but the standard library, keeps no reference
to hardware, and can be tested with made-up numbers. Those three modules hold
almost all the logic, which is why the test suite runs in 30 milliseconds
with no webcam attached.

The clock counts as I/O for this purpose. `main.py` reads `perf_counter()`
once per frame and hands the same instant to everyone that needs it, so a
test can say "held for 1.1 seconds" by passing the number 1.1 rather than
waiting.

---

## The decisions that shaped it

### World landmarks, not image coordinates

mediapipe returns two sets of points per hand: `hand_landmarks`, normalised
0..1 within the image, and `hand_world_landmarks`, real positions in metres
centred on the hand.

Recognition uses the **world** ones. Image coordinates are a shadow: they
change when the hand merely turns.

*Measured:* moving and tilting a hand made the projected palm length swing
from 0.10 to 0.80 — a factor of 8. The same measure in world coordinates
stayed between 0.09 and 0.12 m, which is a real palm.

The preview and the cursor use the **normalised** ones, because they answer a
different question: not *what shape is the hand* but *where is it in the
frame*.

### Smooth the numbers, not the decisions

Landmark positions are averaged over the last few frames before anything
measures them.

mediapipe has to guess where fingers it cannot see are — in a fist they hide
behind the palm and behind each other — and those guesses jump from frame to
frame. A single stray frame changed the recognised gesture, which reset the
hold timer, which meant a command could never accumulate enough time to fire.

Smoothing happens **before** the thresholds on purpose. Once a value has been
compared, 0.58 and 0.62 have become "down" and "up" — two opposite answers —
and no amount of voting afterwards recovers that they were the same reading
with noise on it.

A majority vote over the last few gesture *names* was written as well, to
absorb frames where the pose is genuinely ambiguous. It was never needed once
the landmarks themselves were filtered, and has been removed rather than left
sitting in the module unused.

### The thumb takes no part in recognition

It folds sideways rather than curling, and in a natural fist it rests on the
outside of the other fingers — far enough out to pass every "is it extended?"
test tried, in 2D and in 3D. That made a plain fist register as a thumb
gesture, and **the fist is what switches Hermes off**, so the app could not be
dismissed without curling the thumb inside the fist, which nobody does.

Four fingers that are always right beat five with one that lies. The thumb
still matters for the pinch, but there it is a *distance between two visible
tips*, not a classification.

### 2D for the pinch, 3D for everything else

`pinch_distance` is the one measurement in `gestures.py` that ignores depth.

`z` is the only coordinate mediapipe estimates rather than observes — one
camera cannot see depth — and it degrades first at awkward angles. For a
pinch it is pure noise: two tips that touch are in the same place in the
image, which `x` and `y` report directly.

*Measured:* "fingers touching" ranged 0.1 to 0.5 in 3D and overlapped with
"fingers apart"; in 2D it holds at 0.1 to 0.2 against 0.9 for an open hand.

> There is no universally better choice between 2D and 3D — only the right
> measurement for the question being asked.

Known weakness: seen edge-on, thumb and index can overlap in the image
without touching. It takes deliberate aiming, and a pinch only means anything
in CURSOR state.

### The pointer follows the knuckles, not a fingertip

The four MCP knuckles — landmarks 5, 9, 13, 17 — averaged.

Started as landmark 9 alone, the base of the middle finger, and became the
average of its row for one reason: **the anchor is the number the active zone
multiplies**. The zone is half the frame wide and covers all of the screen, so
on a 1920px monitor one normalised unit is 3840 pixels and 0.001 of landmark
noise is four pixels of visible tremor. Nothing else is amplified like that.

All four are rigid, so averaging them is a *spatial* mean, not a temporal one —
it costs no lag at all, unlike every filter downstream of it. What it removes
is the part of mediapipe's per-landmark noise that is independent between
points. Not all of it: mediapipe regresses the whole hand in one pass, so the
noise is partly shared and the real gain is less than the factor of two the
arithmetic suggests.

The wrist is just as rigid and deliberately left out. Including it drags the
anchor down the hand, and the wrist was already rejected as an anchor for
exactly that reason: with the anchor that low, reaching the edge of the active
zone takes the fingers out of frame and loses the pinch. The centre of the four
knuckles lands next to landmark 9, so the zone stays tuned the way it was.

Fingertips were the first thing tried and the worst: they move when you pinch,
so anchoring there dragged the cursor sideways at the exact moment of
clicking — and a click must not move the pointer.

### Only the middle of the frame maps to the screen

`ZONE_MIN = 0.25`, `ZONE_MAX = 0.75`: the middle half of the camera view covers
100% of the screen, and anything outside clamps to the screen edge.

Started at 0.3/0.7 and was widened while tuning the pointer. The zone is the
gain of the whole chain — the wider it is, the less every pixel of landmark
noise is multiplied — so it turned out to be the most effective anti-tremor
dial in the project, and the one least likely to be looked at.

The corners of the camera's view are neither comfortable to reach nor well
tracked. And because the anchor sits *inside* the hand, pushing it to the very
edge takes the fingers out of frame.

### Strict to start, permissive to continue

The pinch has two phases. Starting a drag requires the pinch closed **and**
the guard satisfied **and** a short dwell. Continuing it requires only that
the pinch is still closed.

Re-checking the guard while dragging would drop the window whenever the other
fingers drifted. Once the intention has been declared, the question changes
from *did the user mean this* to *has the user finished*.

### Two thresholds, never one

`Hysteresis` closes below one value and opens above a higher one; between them
nothing changes. With a single threshold, fingers resting near it flip the
pinch dozens of times a second, and a window gets dropped mid-drag.

The same shape appears wherever a continuous reading becomes a yes/no.

### A low-pass filter cannot make a pointer still

`OneEuroFilter` adapts its cutoff to speed, which is a real improvement over a
fixed average, but it is still **linear**: whatever it removes from a hand at
rest it removes from a hand in motion too. The only choice it offers is where
to sit on the trade between jitter and lag — not how to leave it.

`DeadZone` leaves it. It holds an anchor and reports it unchanged until the
input moves more than a few pixels away, then drags the anchor along behind.
Inside the radius the pointer does not move *at all*; outside it moves at full
speed with nothing added. It is `Hysteresis` in two dimensions applied to a
position instead of a boolean — the same shape, for the same reason.

The cost is an offset of up to `radius` while the pointer travels. At three
pixels nobody sees it.

It also closes a hole left open above: a click must not move the pointer, which
is why the anchor is a knuckle. The palm still shifts slightly as a pinch
closes, and that shift now falls inside the radius instead of reaching the
mouse.

Part of what is left after all this is not noise at all — an unsupported hand
has a real physiological tremor at 8–12 Hz. That is the user's hand, not a bug,
and the dead zone is the only thing here that removes it without paying in lag.

### Describe the state, not the transition

`Cursor.set_pressed(bool)` is called every frame with the desired state, and
only a change reaches the operating system. The alternative — `press()` and
`release()` — forces the caller to detect the edge itself, and getting it
wrong means pressing the button thirty times a second.

The memory of whether the button is down belongs to the mouse, not to the
loop.

### Rules live in tables, not in code

`GESTURES` maps a frozenset of finger names to a gesture name. `TRANSITIONS`
maps `(state, gesture)` to `(new state, seconds it must be held)`. `ACTIONS`
maps a gesture to a key and its timing. `STATE_COLORS` maps a state to a
border colour.

Adding a gesture, a transition or a command is **one line of data**, and the
logic that reads the table never changes. Every one of these started as a
chain of `if`s and became a table when the third case appeared.

A rule that is *not* in the table is often the point. There is deliberately no
`(CURSOR, "fist")` row: while pinching, the fingers read as a fist, so that
rule would end cursor mode mid-drag.

---

## Tried and rejected

Do not re-propose these without new information — each was measured.

| Idea | Why it was dropped |
|---|---|
| **Finger curl** (knuckle-to-tip distance over bone length) | Scale and rotation free, and separated cleanly in isolation — a fist read 0.29 to 0.42 against 0.94 to 1.00 for a straight finger. But it describes *shape*, not *position*: a finger folded down at the knuckle while staying straight reads as extended, and far too many poses registered as an open palm. Combining it with a reach test worked but added no accuracy over the reach test alone. |
| **Gesture orientation** (`point_up` vs `point_down`) | Needs the hand held at a definite angle, which is uncomfortable at a desk and fragile to detect. Sideways poses sat in a dead zone and flickered. |
| **Thumb as a counted finger** | See above — measured in both 2D and 3D, the ranges for open, resting and tucked overlap in both. |
| **3D distance for the pinch** | Ranges overlap; `z` is estimated, not observed. |
| **Normalising by a 2D palm length** | The projected palm collapses under foreshortening — ratios built on it reached 34, which is physically impossible. |
| **mediapipe's `GestureRecognizer`** | Seven canned gestures, robust, and it returns landmarks too. Rejected only because the point of the project is to build the recognition, not to call it. Still the right answer if reliability ever matters more than learning. |
| **Changing the Windows system cursor** to show grip state | Possible via `SetSystemCursor`, but it is global and persists after a crash — the user is left with a changed cursor system-wide. Not worth it here. |
| **A Kalman filter for the pointer** | With one sensor and no real model of how a hand moves, a constant-velocity Kalman converges on what a well-tuned One Euro already does, with more knobs and more code. And it *predicts*, so it overshoots when the hand stops — the worst possible moment for a pointer. |
| **Double exponential / other predictive smoothing** | Same overshoot, more pronounced. They buy back lag by introducing error exactly at the instants that matter: arriving on a target, and clicking. |
| **A longer moving average on the pointer** | Pure lag. `SmoothedLandmarks` lost to One Euro at every setting, and once the pointer stopped using it nothing else did — so it went. |
| **A median filter before One Euro** | Not rejected, just not needed *yet*. It cures isolated single-frame jumps and does nothing against continuous tremor. Add it only if the pointer sits still and occasionally lurches, rather than trembling continuously. |
| **The One Euro defaults from the paper** | `min_cutoff=1.0, beta=0.02` fed normalised coordinates. `beta` scales with the signal, and a hand moves at 1–3 normalised units per second, so the cutoff never left 1 Hz and the adaptation — the entire point of the filter — was switched off. It behaved as a fixed low-pass that was both too slow and too fast. See the tuning procedure below. |

Also worth knowing: **`mp.solutions` no longer exists.** mediapipe 1.0 removed
it, so the majority of tutorials and StackOverflow answers online do not run.
This project uses the Tasks API (`mediapipe.tasks.python.vision`).

---

## What is measured, and what it means

At 640x480 with no processing:

```
FPS: 29.8 | read 19.2 ms | process 0.1 ms | display 14.3 ms
```

`19.2 + 0.1 + 14.3 = 33.6 ms`, and `1000 / 29.8 = 33.6 ms` — the whole frame
is accounted for.

- **The webcam sets the pace, not the code.** 30 fps is what the camera
  delivers; `cap.read()` does not work, it *waits*.
- Real work is about 13 ms out of the 33 available, so mediapipe (5–15 ms)
  fits without dropping frames.
- The preview costs roughly 13 ms — 40% of the real work. It is a debug tool,
  not the application: a silent mode gets all of that back.

The camera only exposes **YUY2**, uncompressed, so raising the resolution
saturates the USB bandwidth rather than the CPU.

---

## Tuning the pointer

Four dials, in the order the numbers travel:

```
palm_point ──► OneEuroLandmarks ──► to_screen ──► DeadZone ──► mouse
 (no dial,       min_cutoff, beta     ZONE_MIN/MAX    radius
  no lag)                              = the gain
```

The tuning below was done against a throwaway jitter meter drawn on the
preview: a sliding window of the last two seconds reporting two numbers in
screen pixels, measured *before* the dead zone — after it the reading at rest
is zero by construction and says nothing.

- **step** — the largest jump between consecutive frames. The shimmer, and
  what `min_cutoff` controls.
- **spread** — the largest excursion across the whole window. Slow drift,
  which no filter that judges by speed can tell from a real slow movement, so
  it survives any amount of low-passing. This is what the dead zone is for.

It has been removed now that the values are settled. It was about twenty lines
— two `deque`s, the peak frame-to-frame distance and the bounding box of the
window — and is worth writing again from scratch before re-tuning, because the
two numbers are what make the steps below possible.

Then, **one dial at a time** — turning two tells you nothing about either:

1. **`beta = 0`**, then lower `min_cutoff` (0.4 → 0.3 → 0.25) until step stops
   falling. Below that you are only buying lag.
2. **Raise `beta`** (4 → 8 → 15) until a fast movement stops feeling dragged.
   Step at rest must not move while you do this; if it does, `beta` is
   reacting to noise and is too high.
3. **Set `radius`** just above the spread you are left with. Typically 2–5.
   Under 2 it does nothing; over 5 fine pointing turns steppy.
4. If tremor still bothers you, **widen the zone**. `ZONE_MIN/MAX` at
   0.25/0.75 takes the gain from 4800 to 3840 px per unit — 20% off everything
   above, at the price of moving the hand further. It is the dial nobody looks
   at and the one with the most direct effect.

Do step 1 before step 2 and not the other way round, or you tune `beta` against
jitter it cannot fix.

**What this machine landed on**, first pass:

| Dial | Value | Where |
|---|---|---|
| cursor `min_cutoff` / `beta` | `0.4` / `4.0` | `main.py` |
| recognition `min_cutoff` / `beta` | `0.25` / `10.0` | `main.py` |
| `DeadZone(radius=)` | `5.0` px | `main.py` |
| `ZONE_MIN` / `ZONE_MAX` | `0.25` / `0.75` | `cursor.py` |

The recognition filter ended up slower and far more adaptive than the cursor
one, which reads oddly until you remember they are fed different units — world
landmarks are metres, so the same `beta` means something else entirely. The
zone was widened from 0.3/0.7 during this pass.

Every threshold in this project that was guessed turned out wrong. Re-measure
after any change to the camera, the resolution or the monitor.

## Conventions

- **Everything inside a file is in English** — identifiers, comments,
  docstrings, error messages, commit messages. The conversation around the
  project happens in Italian.
- **Measure before deciding.** Nearly every number in this project came from
  putting it on screen and looking at it. Thresholds that were guessed have
  all been wrong.
- **Commit messages explain the change; docstrings explain the code.** When a
  decision is surprising — the 2D pinch, the missing `(CURSOR, "fist")` row —
  the reasoning goes in a docstring, because that is where someone about to
  undo it will be looking.
- Files under `tests/` were generated wholesale and say so in their headers.
  The rest was written by hand, with an assistant acting as a tutor.

---

## Current state

Working: activation and deactivation with a safety timeout, three media
commands, cursor movement, click and drag by pinching.

| State | Entered by | Left by |
|---|---|---|
| `IDLE` | start, or fist held 1 s, or 3 s with no hand | open palm held 1 s |
| `ACTIVE` | open palm | fist, no hand, or pointing |
| `CURSOR` | pointing 0.5 s | open palm 0.5 s, or 3 s with no hand |

Not done, in rough order of importance:

- `cursor.py`, `actions.py`, `hand.py` and the pinch helpers have **no tests**.
  A tautology in the first draft of the pinch guard made it always return true;
  a test would have caught it in seconds. `HandSelector` is the newest gap and
  the easiest to fill — it is pure logic over a mediapipe result, and its
  index-0 and hand-absent branches were both wrong on the first attempt.
  (`palm_point` and `DeadZone` are covered, in `test_pointer.py`.)
- The cursor maps to the **primary monitor only**; the desktop spans two.
- No configuration file — every threshold is a constant in a module.
- No feedback that does not require looking at the preview. A short beep on
  entering and leaving ACTIVE would work while reading a book; a coloured
  border does not.
- The gesture vocabulary has grown to eight entries, several of which are
  awkward to perform and none of which have been pruned.
