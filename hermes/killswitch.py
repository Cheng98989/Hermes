from pynput import keyboard

class KillSwitch:
    """Global ESC listener: works even when the preview window is not focused."""

    def __init__(self) -> None:
        self.triggered = False
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def _on_press(self, key) -> None:
        # runs on the listener's own thread: only set a flag here
        if key == keyboard.Key.esc:
            self.triggered = True

    def stop(self) -> None:
        self._listener.stop()