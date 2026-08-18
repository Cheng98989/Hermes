import time
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QSoundEffect

from hermes.config import AUDIO_STATES


class AudioManager(QObject):
    requested = Signal(str)

    def __init__(self, audio_volume: float) -> None:
        super().__init__()
        self.sounds: dict[str, QSoundEffect] = {}
        for key, path in AUDIO_STATES.items():
            self.sounds[key] = load_audio(str(path), audio_volume)
        self.requested.connect(self._play)

    # two halves, because the sounds belong to the main thread: the worker only
    # emits, and Qt queues the call so that _play runs where the sounds live.
    # Reaching them from the worker instead raises "QWinEventNotifier: Event
    # notifiers cannot be enabled or disabled from another thread"
    def play(self, state: str) -> None:
        self.requested.emit(state)

    @Slot(str)
    def _play(self, state: str) -> None:
        sound = self.sounds.get(state)

        if sound is None:
            return
        
        sound.play()


def load_audio(path: str, global_volume: float) -> QSoundEffect:
    sound = QSoundEffect()

    sound.setSource(QUrl.fromLocalFile(path))
    sound.setVolume(global_volume)

    return sound
