"""Global listener: works even when the preview window is not focused."""

from pynput import keyboard


class Listener:
    def __init__(self) -> None:
        self.quit = False
        self.pause = False
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()

    def _on_press(self, key) -> None:
        # runs on its own thread: only set a flag here
        if key == keyboard.Key.esc:
            self.quit = True
        if key == keyboard.Key.f12:
            self.pause = not self.pause

    def stop(self) -> None:
        self._listener.stop()
