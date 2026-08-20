"""Handle configuration saving and loading"""

import sys
import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

CONFIG_DIR = Path(os.environ["APPDATA"]) / "Hermes"
CONFIG_PATH = CONFIG_DIR / "config.json"

BUNDLE = getattr(sys, "_MEIPASS", None)
ROOT = Path(BUNDLE) if BUNDLE else Path(__file__).parent.parent
ICON_PATH = ROOT / "assets" / "icon.png"
MODEL_PATH = ROOT / "models" / "hand_landmarker.task"


NO_SIGNAL_FRAME_PATH = ROOT / "assets" / "no_signal_frame.png"


# STATES
IDLE = "IDLE"
ACTIVE = "ACTIVE"
CURSOR = "CURSOR"
SCROLL = "SCROLL"
UNKNOWN = "UNKNOWN"

STATES = {IDLE, ACTIVE, CURSOR, SCROLL}


# Audio
# the folder comes first so that the sounds can be made configurable later:
# every state change rings, and each ring should be swappable
# TODO: audio configurabile, ogni transizione allo stato x puo avere un suono
# si potrebbe mettere di default note del piano diverse e poi configurabili compreso volume singolo
AUDIO_FOLDER = ROOT / "assets" / "audio"

AUDIO_IDLE = AUDIO_FOLDER / "bell_ring.wav"
AUDIO_ACTIVE = AUDIO_FOLDER / "bell_ring.wav"
AUDIO_CURSOR = AUDIO_FOLDER / "bell_ring.wav"
AUDIO_SCROLL = AUDIO_FOLDER / "bell_ring.wav"
AUDIO_UNKNOWN = AUDIO_FOLDER / "bell_ring.wav"

AUDIO_STATES = {
    IDLE: AUDIO_IDLE,
    ACTIVE: AUDIO_ACTIVE,
    CURSOR: AUDIO_CURSOR,
    SCROLL: AUDIO_SCROLL,
    UNKNOWN: AUDIO_UNKNOWN,
}


BASICS = (
    "camera_index", "audio_volume", "camera_faces_you", "screen", "hand", "zone_min",
    "zone_max",
    "cursor_dead_zone_radius", "pinch_close", "pinch_open", "pinch_dwell",
    "pinky_pinch_close", "pinky_pinch_open", "pinky_ready_close", "pinky_ready_open",
    "fingers_joined", "fingers_apart", "scroll_speed", "scroll_span",
    "scroll_dead_zone",
)
PREVIEW = ("show_preview", "show_skeleton", "show_debug_text", "show_mapping_area")

CAMERA_INDEX = "camera_index"
SCREEN = "screen"

LABELS = {
    "camera_index": ("Camera", "Which webcam, counting from zero"),
    "audio_volume": ("Audio volume", "Volume of the audio feedback played during states transition"),
    "camera_faces_you": ("Camera faces you", "Mirror the picture; off if it looks away"),
    "screen": ("Screen", "Which monitor the active zone covers; All spans the desktop"),
    "hand": ("Hand", "Which hand Hermes obeys; the other is ignored"),
    "zone_min": ("Active zone start", "The part of the picture that covers the screen"),
    "zone_max": ("Active zone end", "Wider means finer control but more hand travel"),
    "cursor_dead_zone_radius": ("Pointer steadiness", "Pixels before the pointer follows"),
    "pinch_close": ("Pinch to click", "How close thumb and index must be to press"),
    "pinch_open": ("Pinch to release", "How far apart to let go; must exceed the above"),
    "pinch_dwell": ("Pinch delay", "Seconds to hold before the click registers"),
    "pinky_pinch_close": ("Pinky pinch to right click", "How close thumb and little finger must be"),
    "pinky_pinch_open": ("Pinky pinch release", "How far apart to let go; must exceed the above"),
    "pinky_ready_close": ("Right click ready", "Thumb this near the pinky keeps Cursor mode"),
    "pinky_ready_open": ("Right click ready release", "How far the thumb spreads to leave it"),
    "fingers_joined": ("Fingers together", "How close index and middle must be to scroll"),
    "fingers_apart": ("Fingers apart", "How far apart they must be to stop scrolling"),
    "scroll_speed": ("Scroll speed", "Clicks per second at full tilt"),
    "scroll_span": ("Scroll range", "How far to tilt to reach full speed"),
    "scroll_dead_zone": ("Scroll deadzone", "Drift allowed before scrolling starts"),
    "show_preview": ("Open preview at start", ""),
    "show_skeleton": ("Draw the hand skeleton", ""),
    "show_debug_text": ("Draw the debug lines", ""),
    "show_mapping_area": ("Draw the active zone", ""),
    "min_hand_detection_confidence": ("Detection confidence", "How sure before reporting a hand"),
    "min_hand_presence_confidence": ("Presence confidence", "How sure the hand is still there"),
    "min_tracking_confidence": ("Tracking confidence", "How sure to keep following the same hand"),
    "cursor_min_cutoff": ("Pointer smoothing", "Lower is steadier at rest, at the cost of lag"),
    "cursor_beta": ("Pointer responsiveness", "Higher follows fast movement more closely"),
    "world_min_cutoff": ("Recognition smoothing", "The same, for the gesture recogniser"),
    "world_beta": ("Recognition responsiveness", "Beta scales with the signal; this one is metres"),
}

# the fixed options of a drop-down
CHOICES = {
    "hand": ("Right", "Left"),
}

# Name: (min, max, step, decimals)
RANGES = {
    "camera_index": (0, 10, 1, 0),
    "audio_volume": (0, 1, 0.05, 2),
    "zone_min": (0.0, 1.0, 0.05, 2),
    "zone_max": (0.0, 1.0, 0.05, 2),
    "cursor_dead_zone_radius": (0.0, 50.0, 0.5, 1),
    "pinch_close": (0.0, 3.0, 0.01, 2),
    "pinch_open": (0.0, 3.0, 0.01, 2),
    "pinch_dwell": (0.0, 5.0, 0.05, 2),
    "pinky_pinch_close": (0.0, 3.0, 0.01, 2),
    "pinky_pinch_open": (0.0, 3.0, 0.01, 2),
    "pinky_ready_close": (0.0, 3.0, 0.01, 2),
    "pinky_ready_open": (0.0, 3.0, 0.01, 2),
    "fingers_joined": (0.0, 3.0, 0.01, 2),
    "fingers_apart": (0.0, 3.0, 0.01, 2),
    "scroll_speed": (1.0, 60.0, 1.0, 1),
    "scroll_span": (0.01, 1.0, 0.01, 2),
    "scroll_dead_zone": (0.0, 1.0, 0.01, 2),
    "min_hand_detection_confidence": (0.0, 1.0, 0.05, 2),
    "min_hand_presence_confidence": (0.0, 1.0, 0.05, 2),
    "min_tracking_confidence": (0.0, 1.0, 0.05, 2),
    "cursor_min_cutoff": (0.01, 10.0, 0.05, 2),
    "cursor_beta": (0.0, 50.0, 0.5, 2),
    "world_min_cutoff": (0.01, 10.0, 0.05, 2),
    "world_beta": (0.0, 50.0, 0.5, 2),
}
# A < B
ORDERED_PAIRS = (
    ("zone_min", "zone_max"),
    ("pinch_close", "pinch_open"),
    ("pinky_pinch_close", "pinky_pinch_open"),
    ("pinky_ready_close", "pinky_ready_open"),
    ("fingers_joined", "fingers_apart"),
    ("scroll_dead_zone", "scroll_span"),
)


def limits(name: str) -> tuple[float, float, float, int]:
    return RANGES.get(name, (0.0, 100.0, 0.01, 3))


def broken_pairs(config: "Config") -> list[str]:
    wrong = []
    for low, high in ORDERED_PAIRS:
        if getattr(config, low) >= getattr(config, high):
            first, _ = label_and_tip(low)
            second, _ = label_and_tip(high)
            wrong.append(f"[{first}] must be less than [{second}]")
    return wrong


def label_and_tip(name: str) -> tuple[str, str]:
    return LABELS.get(name, (name.replace("_", " ").capitalize(), ""))


@dataclass
class Config:
    # --- basics --------------------------------------------------------------
    camera_index: int = 0
    audio_volume: float = 0.6
    camera_faces_you: bool = True
    screen: str = "Primary"
    hand: str = "Right"
    zone_min: float = 0.25
    zone_max: float = 0.75
    cursor_dead_zone_radius: float = 20.0
    pinch_close: float = 0.25
    pinch_open: float = 0.35
    pinch_dwell: float = 0.0
    pinky_pinch_close: float = 0.20
    pinky_pinch_open: float = 0.35
    pinky_ready_close: float = 1.0
    pinky_ready_open: float = 1.15
    fingers_joined: float = 0.20
    fingers_apart: float = 0.30
    scroll_speed: float = 12.0
    scroll_span: float = 0.18
    scroll_dead_zone: float = 0.03

    # --- preview -------------------------------------------------------------
    show_preview: bool = True
    show_skeleton: bool = True
    show_debug_text: bool = True
    show_mapping_area: bool = True
    state_colors: dict[str, list[int]] = field(default_factory=lambda: {
        # BGR
        "IDLE":   [0, 0, 255],        # red
        "ACTIVE": [0, 255, 0],        # green
        "CURSOR": [255, 0, 0],        # blue
        "SCROLL": [0, 255, 255],      # yellow
        "UNKNOWN": [128, 128, 128],    # grey
    })

    # --- advanced ------------------------------------------------------------
    min_hand_detection_confidence: float = 0.5
    min_hand_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    cursor_min_cutoff: float = 0.25
    cursor_beta: float = 10.0
    world_min_cutoff: float = 0.25
    world_beta: float = 10.0


def save(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(asdict(config), indent=2)
    CONFIG_PATH.write_text(text, encoding="utf-8")


def check_config(config: Config) -> list[str]:
    # At the moment it is the same as broken pairs but there could be add some other chekers
    errors = broken_pairs(config)
    return errors


def load() -> Config:
    try:
        text = CONFIG_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        config = Config()
        save(config)
        return config

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return Config()

    valid = set()
    for f in fields(Config):
        valid.add(f.name)

    filtered = {}
    for key, value in data.items():
        if key in valid:
            filtered[key] = value
    return Config(**filtered)
