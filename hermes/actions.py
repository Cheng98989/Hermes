from pynput.keyboard import Controller, Key

COMMAND_DWELL = 0.3      # seconds a gesture must be held to count as a command

ACTIONS = {
    "thumb_up": Key.media_volume_up,
}


class Actions:
    """Turns a gesture name into a keystroke on the real system."""

    def __init__(self) -> None:
        self._keyboard = Controller()

    def run(self, gesture: str) -> bool:
        key = ACTIONS.get(gesture)
        if key is not None:
            self._keyboard.press(key)
            self._keyboard.release(key)
            return True
        return False