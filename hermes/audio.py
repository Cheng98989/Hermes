from pathlib import Path
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtMultimedia import QSoundEffect

from hermes.config import Config, DEFAULT_AUDIO, audio_path


class AudioManager(QObject):
    requested = Signal(str)

    def __init__(self, config: Config, audio_volume: float) -> None:
        super().__init__()
        self.config = config
        self.sounds: dict[str, QSoundEffect] = {}
        for state, name in self.config.state_audio.items():
            self.sounds[state] = load_audio(audio_path(name, state), audio_volume)
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


def load_audio(path: Path, global_volume: float) -> QSoundEffect:
    sound = QSoundEffect()

    def check_errors() -> None:
        if (
            sound.status() == QSoundEffect.Status.Error and
            sound.source() != QUrl.fromLocalFile(str(DEFAULT_AUDIO))
        ):
            print(f"Failed to load: {path}, loading defautl audio.")
            sound.setSource(QUrl.fromLocalFile(str(DEFAULT_AUDIO)))

    sound.statusChanged.connect(check_errors)

    sound.setSource(QUrl.fromLocalFile(path))
    sound.setVolume(global_volume)

    return sound
    
