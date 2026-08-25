# Iris

*Control your desktop in a different way.*

[🇬🇧 English](README.md) · [🇮🇹 Italiano](README.it.md)

## Table of contents
- [What is Iris](#what-is-iris)
- [Privacy notice](#privacy-notice)
- [Quick start](#quick-start)
- [How to use it](#how-to-use-it)
- [States and gestures](#states-and-gestures)
- [Settings](#settings)
- [Uninstalling](#uninstalling)
- [Building from source](#building-from-source)
- [License](#license)
- [Development notes](#development-notes)
- [Contact](#contact)

## What is Iris

Ever eaten in front of your PC with greasy hands and still wanted to switch tabs, change the volume, or pause a video, without cleaning your hands first to touch the mouse and keyboard? Or maybe your desk is small, and while you study or work, the mouse and keyboard end up pushed somewhere awkward to reach?

Iris was built for exactly that: it uses your webcam to recognize hand gestures and lets you control the cursor and a few desktop functions with gestures, without touching anything.

## Privacy notice

**Iris does not collect or send webcam images over the Internet.** All processing happens locally, on your own computer.

## Quick start

Iris has currently only been tested on **Windows 11**. All you need is a working webcam.

There's no installer:
1. Download the `.zip`.
2. Extract it into a folder of your choice.
3. Run `Iris.exe`.

On first launch, Iris automatically creates a configuration file with default values.

## How to use it

On startup a terminal window opens — **it must stay open**: closing it closes the app too — and after a moment, the preview window with the camera stream appears. If Iris can't find any webcam, the preview shows an error message. Closing the preview window doesn't close Iris: the app keeps running in the background.

Click Iris' icon in the system tray to open the dropdown menu, which has three options:
- **Preview** — show or hide the preview window.
- **Settings** — open the settings panel.
- **Quit** — actually close the application.

> **Warning:** in case of misrecognized gestures that could cause issues, the **Esc** key on your keyboard is always listened for and will close the app even while it's running in the background.

## States and gestures

Iris works as a state machine: at any moment you're in one specific state, and only certain gestures — held for a set number of seconds — move you to the next one.

| State | What it does | How to enter it |
|---|---|---|
| **Idle** | Resting state: Iris watches but doesn't interact with the desktop. | Starting state. |
| **Active** | Recognizes gestures for volume up/down and play/pause (see table below). | From Idle, open palm held for 1 s. |
| **Cursor** | The mouse pointer follows your hand; pinching (thumb + index) clicks and drags. | From Active, index finger only extended, for 0.5 s. |
| **Scroll** | Scroll by moving your hand above or below a reference line. | From Cursor, index and middle fingers extended and together, for 0.3 s. |
| **Unknown** | A state that, bugs aside, should never appear. | — |

To go back:
- From **Cursor** to **Active**: open palm, 0.5 s.
- From **Scroll** to **Cursor**: spread your fingers (index and middle apart) or extend only your index finger, 0.2 s.
- From **Scroll** to **Active**: open palm, 0.5 s.
- From **Active** to **Idle**: closed fist (1 s).
- From **Cursor**, **Active**, or **Scroll** to **Idle**: hand no longer detected, for 3 s.

In the **Active** state, some gestures trigger an action directly (not a state change):

| Gesture | Action | Notes |
|---|---|---|
| Index and middle extended and apart (*victory*) | Volume up | Held 0.5 s, then repeats every 0.3 s while held |
| Index, middle, and ring extended (*three*) | Volume down | Held 0.5 s, then repeats every 0.3 s |
| Index and pinky extended (*rock*) | Media play/pause | Held 0.5 s, a single action with no repeat |

In the **Cursor** state, the pointer follows the average position of the middle, ring, and pinky knuckles. Pinching (bringing thumb and index together) starts a drag; spreading the fingers apart again ends it (release). Author's tip: for more accurate pinch recognition, show your hand to the camera at a slightly oblique angle rather than head-on.

In the **Scroll** state, the preview shows a yellow line at the height of your index and middle fingertips: move your hand below that line to scroll down, above it to scroll up.

At the moment, hold times and the gestures tied to states and actions aren't configurable from the interface: changing them requires editing the source code.

## Settings

Every parameter has a tooltip (hover over it to read). If a tooltip is missing or unclear, feel free to report it.

| Parameter | Description |
|---|---|
| Camera | Which webcam to use, counting from zero. |
| Camera faces you | Mirrors the image; turn off if the webcam doesn't face you. |
| Hand | Which hand Iris follows; the other is ignored. |
| Active zone start / end | The portion of the frame that maps to the screen; a wider zone gives finer control but needs more hand travel. |
| Pointer steadiness | Minimum pixel movement before the pointer starts following your hand. |
| Pinch to click | How close thumb and index must get to register a click. |
| Pinch to release | How far apart they must get to release the click; must be larger than the threshold above. |
| Pinch delay | Seconds to hold before the click registers. |
| Fingers together | How close index and middle must be to trigger scrolling. |
| Fingers apart | How far apart they must be to stop scrolling. |
| Scroll speed | Scroll clicks per second at full tilt. |
| Scroll range | How far to tilt your hand to reach full speed. |
| Scroll deadzone | Tolerance margin before scrolling actually starts. |
| Open preview at start | Show the preview window on launch. |
| Draw the hand skeleton | Draws the hand skeleton in the preview. |
| Draw the debug lines | Shows debug information in the preview. |
| Draw the active zone | Draws the active zone in the preview. |
| Detection confidence | How confident Iris must be before reporting a detected hand. |
| Presence confidence | How confident it must be that the hand is still present. |
| Tracking confidence | How confident it must be to keep following the same hand. |
| Pointer smoothing | Lower values keep the pointer steadier at rest, at the cost of more lag. |
| Pointer responsiveness | Higher values follow fast movements more closely. |
| Recognition smoothing | Same idea, for gesture recognition. |
| Recognition responsiveness | Beta scales with the signal; here the unit is metres. |

To restore the default values, at the moment you need to manually delete the configuration file:
1. Press `Win + R`, type (or paste) the following path, and press Enter:
   ```
   %appdata%
   ```
2. Go into the `Iris` folder and delete `config.json`.
3. Restart Iris: the file will be recreated with default values.

## Uninstalling

1. Delete the folder where you extracted Iris.
2. If you also want to remove the configuration data, delete the `Iris` folder inside `%appdata%` too.

## Building from source

Clone the repository:
```
git clone https://github.com/Cheng98989/Iris.git
cd Iris
```

Create/activate a Python environment (developed with 3.11.8) and install the required dependencies, including `pyinstaller`. Then build:
```
pyinstaller Iris.spec
```

The output — everything needed to run the app — will be in the `dist` folder.

## License

Distributed under the **GPL-3.0-or-later** license. Full text in [LICENCE.txt](LICENCE.txt).

## Development notes

The project started as a way to learn Python; it's also a school project, so whether development continues (also) depends on my discipline — there's no guarantee of ongoing maintenance.

While developing, I used AI as support, mainly for learning purposes: no vibecoding — the AI was a sounding board to discuss functions and solve problems, not something that wrote the project for me. AI was also used for documentation in the source code and the README; the final content has been reviewed by me either way.

Built with:
- Python 3.11.8
- PySide6
- MediaPipe
- OpenCV
- Pynput

## Contact

For bug reports, questions, or suggestions, open an issue on GitHub.
