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

BASICS = (
    "camera_index", "camera_faces_you", "hand", "zone_min", "zone_max",
    "cursor_dead_zone_radius", "pinch_close", "pinch_open", "pinch_dwell",
    "fingers_joined", "fingers_apart", "scroll_speed", "scroll_span",
    "scroll_dead_zone",
)
PREVIEW = ("show_preview", "show_skeleton", "show_debug_text", "show_mapping_area")

LABELS = {
    "camera_index": ("Camera", "Which webcam, counting from zero"),
    "camera_faces_you": ("Camera faces you", "Mirror the picture; off if it looks away"),
    "hand": ("Hand", "Which hand Hermes obeys; the other is ignored"),
    "zone_min": ("Active zone start", "The part of the picture that covers the screen"),
    "zone_max": ("Active zone end", "Wider means finer control but more hand travel"),
    "cursor_dead_zone_radius": ("Pointer steadiness", "Pixels before the pointer follows"),
    "pinch_close": ("Pinch to click", "How close thumb and index must be to press"),
    "pinch_open": ("Pinch to release", "How far apart to let go; must exceed the above"),
    "pinch_dwell": ("Pinch delay", "Seconds to hold before the click registers"),
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

def label_and_tip(name: str) -> tuple[str, str]:
    return LABELS.get(name, (name.replace("_", " ").capitalize(), ""))

@dataclass
class Config:
    # --- basics --------------------------------------------------------------
    camera_index: int = 0
    camera_faces_you: bool = True
    hand: str = "Right"
    zone_min: float = 0.25
    zone_max: float = 0.75
    cursor_dead_zone_radius: float = 5.0
    pinch_close: float = 0.20
    pinch_open: float = 0.30
    pinch_dwell: float = 0.0
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
