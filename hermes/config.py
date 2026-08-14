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
