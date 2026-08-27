"""Iris's UI"""

import cv2
from dataclasses import fields
import numpy as np
import pathlib

from PySide6.QtCore import Qt, QSize, QTimer, Signal, SignalInstance
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QDialogButtonBox,
    QLineEdit,
    QFileDialog,
    QToolButton,
    QStyle,
)

from iris.audio import AudioPlayer
from iris.config import (
    BASICS,
    CAMERA_INDEX,
    CHOICES,
    NO_SIGNAL_FRAME_PATH,
    PREVIEW,
    AUDIO,
    SCREEN,
    LIVE,
    DEFAULT_AUDIO,
    Config,
    check_config,
    label_and_tip,
    limits,
    save,
    audio_path,
    store_sound,
    is_playable_wav,
)

_no_signal = cv2.imread(str(NO_SIGNAL_FRAME_PATH))
NO_SIGNAL_FRAME = _no_signal if _no_signal is not None else np.zeros((720, 1280, 3), dtype=np.uint8)


def make_widget(name: str, value):
    min_value, max_value, step, decimals = limits(name)

    if isinstance(value, bool):
        widget = QCheckBox()
        write_widget(name, widget, value)
        return widget

    if isinstance(value, int):
        if name == CAMERA_INDEX:
            widget = QComboBox()
        else:
            widget = QSpinBox()
            widget.setRange(int(min_value), int(max_value))
        write_widget(name, widget, value)
        return widget

    if isinstance(value, float):
        widget = QDoubleSpinBox()
        widget.setRange(min_value, max_value)
        widget.setDecimals(decimals)
        widget.setSingleStep(step)
        write_widget(name, widget, value)
        return widget

    if isinstance(value, str):
        widget = QComboBox()
        widget.addItems(CHOICES.get(name, (value,)))
        write_widget(name, widget, value)
        return widget

    return None


def read_widget(name: str, widget):
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        if name == CAMERA_INDEX:
            return int(widget.currentText() or 0)
        return widget.currentText()

    return widget.value()


def write_widget(name: str, widget, value) -> None:
    if isinstance(widget, QCheckBox):
        widget.setChecked(value)
        return
    if isinstance(widget, QComboBox):
        if name == CAMERA_INDEX:
            widget.setCurrentText(str(value))
        else:
            widget.setCurrentText(value)
        return

    widget.setValue(value)

def changed_signal(widget) -> SignalInstance:
    if hasattr(widget, "changed"):
        return widget.changed
    if isinstance(widget, QCheckBox):
        return widget.toggled
    if isinstance(widget, QComboBox):
        return widget.currentTextChanged

    return widget.valueChanged


# the config keeps colours the way OpenCV wants them, blue first
def list_to_color(bgr: list[int]) -> QColor:
    return QColor(bgr[2], bgr[1], bgr[0])

def set_row_visible(control, visible: bool) -> None:
    host = control.parent()
    host.parent().layout().setRowVisible(host, visible)

def in_a_row(*widgets) -> QWidget:
    host = QWidget()
    row = QHBoxLayout(host)
    row.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        row.addWidget(widget)

    return host


class RestoreButton(QToolButton):
    def __init__(self, read, write, default) -> None:
        super().__init__()
        self.read = read
        self.write = write
        self.default = default
        self.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.setToolTip("Back to the default")
        self.clicked.connect(self.restore)
        self.refresh()

    def restore(self) -> None:
        self.write(self.default)
        # set_bgr and set_path_text emit nothing, so nobody else would
        self.refresh()

    def refresh(self) -> None:
        self.setVisible(self.read() != self.default)


class ColorButton(QPushButton):
    changed = Signal()
    def __init__(self, bgr: list[int]) -> None:
        super().__init__()
        self.color = list_to_color(bgr)
        self.setIconSize(QSize(40, 16))
        self.refresh()
        self.clicked.connect(self.pick)

    def refresh(self) -> None:
        icon = QPixmap(self.iconSize())
        icon.fill(self.color)
        self.setIcon(QIcon(icon))

    def pick(self) -> None:
        chosen = QColorDialog.getColor(
            self.color,
            self.window(),
            options=QColorDialog.ColorDialogOption.DontUseNativeDialog,
        )
        if chosen.isValid():
            self.color = chosen
            self.refresh()
            self.changed.emit()

    def bgr(self) -> list[int]:
        return [self.color.blue(), self.color.green(), self.color.red()]

    def set_bgr(self, bgr: list[int]) -> None:
        self.color = list_to_color(bgr)
        self.refresh()

class FileButton(QToolButton):
    changed = Signal()
    def __init__(self, label: QLineEdit, state: str) -> None:
        super().__init__()
        self.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.setToolTip("Choose a sound")
        self.clicked.connect(self.pick)
        self.label = label
        self.state = state
        self.name = ""
        self.reset()

    def default_path(self) -> pathlib.Path:
        return audio_path("", self.state)

    def pick(self) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter("WAV files (*.wav)")
        if dialog.exec() and is_playable_wav(dialog.selectedFiles()[0]):
            self.path_string = dialog.selectedFiles()[0]
            self.set_path_text(pathlib.Path(self.path_string))
            self.changed.emit()

    def set_path_text(self, path: pathlib.Path) -> None:
        if not path.exists():
            path = self.default_path()
        self.label.setText(path.name)

    def value(self) -> str:
        return self.path_string or self.name

    def reset(self) -> None:
        self.path_string = ""

    def restore_default(self, _unused: str = "") -> None:
        self.path_string = ""
        self.name = ""
        self.label.setText(self.default_path().name)

class Preview(QLabel):
    def __init__(self, shared, width: int, height: int, preview_refresh_time: int = 33) -> None:
        super().__init__()
        self.shared = shared
        self.setWindowTitle("Iris")
        self.resize(width, height)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(preview_refresh_time)

    def refresh(self) -> None:
        frame = self.shared.frame

        if self.shared.camera_lost:
            frame = NO_SIGNAL_FRAME

        if frame is None:
            return

        height, width = frame.shape[:2]
        image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(image)
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class Settings(QDialog):
    def __init__(self, config: Config, get_camera, get_screens, on_restart) -> None:
        super().__init__()
        self.config = config
        self.get_camera = get_camera
        self.get_screens = get_screens
        self.on_restart = on_restart
        self.setWindowTitle("Iris settings")
        self.setMinimumWidth(360)
        self.widgets = {}
        self.color_buttons = {}
        self.file_buttons = {}
        self.restore_buttons = []
        self.defaults = Config()
        self.audio_player = AudioPlayer()

        self.forms = {
            "Basics": QFormLayout(),
            "Preview": QFormLayout(),
            "Audio": QFormLayout(),
            "Advanced": QFormLayout(),
        }

        for field in fields(Config):
            widget = make_widget(field.name, getattr(config, field.name))
            if widget is None:
                continue

            if field.name in BASICS:
                page_name = "Basics"
            elif field.name in PREVIEW:
                page_name = "Preview"
            elif field.name in AUDIO:
                page_name = "Audio"
            else:
                page_name = "Advanced"

            label, tip = label_and_tip(field.name)
            text = QLabel(label)
            text.setToolTip(tip)
            widget.setToolTip(tip)

            restore = RestoreButton(
                lambda n=field.name, w=widget: read_widget(n, w),
                lambda value, n=field.name, w=widget: write_widget(n, w, value),
                getattr(self.defaults, field.name),
            )
            changed_signal(widget).connect(restore.refresh)

            self.forms[page_name].addRow(text, in_a_row(widget, restore))
            self.widgets[field.name] = widget
            self.restore_buttons.append(restore)

        for state, bgr in config.state_colors.items():
            button = ColorButton(bgr)
            restore = RestoreButton(
                button.bgr, button.set_bgr, self.defaults.state_colors[state]
            )
            button.changed.connect(restore.refresh)

            self.forms["Preview"].addRow(
                QLabel(state.capitalize()), in_a_row(button, restore)
            )
            self.color_buttons[state] = button
            self.restore_buttons.append(restore)

        for state, name in config.state_audio.items():
            label = QLabel(state.capitalize())
            play_button = QToolButton()
            play_button.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            )
            play_button.setToolTip("Play")
            play_button.clicked.connect(lambda _=False, s=state: self.play_sound(s))

            wav_name = QLineEdit()
            wav_name.setReadOnly(True)
            file_button = FileButton(wav_name, state)
            file_button.set_path_text(audio_path(name, state))
            restore = RestoreButton(
                file_button.value, file_button.restore_default, ""
            )
            file_button.changed.connect(restore.refresh)

            self.forms["Audio"].addRow(
                label, in_a_row(wav_name, restore, play_button, file_button)
            )
            self.restore_buttons.append(restore)
            self.file_buttons[state] = file_button

        self.tabs = QTabWidget()

        for page_name, form in self.forms.items():
            page = QWidget()
            page.setLayout(form)

            scroll = QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            self.tabs.addTab(scroll, page_name)
        self.tabs_label_update()

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )

        box.accepted.connect(self.save_settings)
        box.rejected.connect(self.close)
        restore = box.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        restore.clicked.connect(self.restore_defaults)

        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search settings")
        search_bar.setClearButtonEnabled(True)
        search_bar.textChanged.connect(self.filter_widgets)

        outer = QVBoxLayout()
        outer.addWidget(search_bar)
        outer.addWidget(self.tabs)
        outer.addWidget(box)
        self.setLayout(outer)


    def fill_widgets(self, config: Config) -> None:
        for name, widget in self.widgets.items():
            write_widget(name, widget, getattr(config, name))

        for state, button in self.color_buttons.items():
            color = config.state_colors.get(state)
            if color is not None:
                button.set_bgr(color)

        for state, button in self.file_buttons.items():
            wav = config.state_audio.get(state)
            if wav is None:
                continue

            button.set_path_text(audio_path(wav, state))
            button.name = wav
            button.reset()

        # the signals say when a value changes, not how it stands now
        for restore in self.restore_buttons:
            restore.refresh()
            
    def sound_for(self, state: str) -> pathlib.Path:
        picked = self.file_buttons[state].path_string
        if picked:
            return pathlib.Path(picked)

        return audio_path(self.config.state_audio.get(state, ""), state)

    def play_sound(self, state: str) -> None:
        volume = read_widget("audio_volume", self.widgets["audio_volume"])
        if not self.audio_player.play(self.sound_for(state), float(volume)):
            QMessageBox.warning(
                self, "Sound not playable", f"{self.sound_for(state)}"
            )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.fill_widgets(self.config)
        QTimer.singleShot(0, self.refresh_cameras)
        QTimer.singleShot(0, self.refresh_screens)

    def refresh_cameras(self) -> None:
        combo = self.widgets.get(CAMERA_INDEX)
        if combo is None:
            return

        wanted = combo.currentText() or str(self.config.camera_index)
        available = self.get_camera()

        combo.clear()
        combo.addItems([str(index) for index in available] or [wanted])
        combo.setEnabled(bool(available))
        combo.setCurrentText(wanted)

    def refresh_screens(self) -> None:
        combo = self.widgets.get(SCREEN)
        if combo is None:
            return

        wanted = combo.currentText() or self.config.screen
        combo.clear()
        combo.addItems(self.get_screens())
        combo.setCurrentText(wanted)

    def save_settings(self) -> None:
        restart_on_save = False
        for name, widget in self.widgets.items():
            new_value = read_widget(name, widget)
            if getattr(self.config, name) != new_value and name not in LIVE:
                restart_on_save = True
            setattr(self.config, name, new_value)

        for state, button in self.color_buttons.items():
            new_value = button.bgr()
            if self.config.state_colors[state] != new_value:
                restart_on_save = True
            self.config.state_colors[state] = new_value

        unstored = []
        for state, button in self.file_buttons.items():
            if button.path_string:
                # the chosen file may no longer be there
                try:
                    new_wav = store_sound(button.path_string)
                except Exception as problem:
                    unstored.append(f"{state.capitalize()}: {problem}")
                    continue
            else:
                # empty after a reset, unchanged when nobody touched it
                new_wav = button.name

            if self.config.state_audio[state] != new_wav:
                restart_on_save = True
            self.config.state_audio[state] = new_wav

        errors = check_config(self.config)
        if errors:
            errors = "\n".join(errors)
            QMessageBox.warning(self, "Failed to save some options", errors)
            return

        # on problems the user can choose to edit their settings or save the rest
        if unstored:
            answer = QMessageBox.warning(
                self,
                "Some sounds were not saved",
                "\n".join(unstored)
                + "\n\nSave the rest anyway, or go back and edit?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )

            if answer != QMessageBox.StandardButton.Ok:
                return

        save(self.config)

        if restart_on_save:
            answer = QMessageBox.question(
                self,
                "Restart Iris",
                "Some of the saved settings only apply after a restart."
                " Restart now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            restart_on_save = answer == QMessageBox.StandardButton.Yes

        self.close()

        if restart_on_save:
            self.on_restart()

    def restore_defaults(self) -> None:
        self.fill_widgets(Config())

    def filter_widgets(self, text: str) -> None:
        text = text.casefold()

        for name, widget in self.widgets.items():
            label, tip = label_and_tip(name)
            searchable = f"{name} {label} {tip}".casefold()
            set_row_visible(widget, text in searchable)

        for state, button in self.color_buttons.items():
            set_row_visible(button, text in state.casefold())

        for state, button in self.file_buttons.items():
            set_row_visible(button, text in state.casefold())

        self.tabs_label_update()

    def tabs_label_update(self) -> None:
        for i, (name, form) in enumerate(self.forms.items()):
            visible = sum(form.isRowVisible(r) for r in range(form.rowCount()))
            self.tabs.setTabText(i, f"{name} ({visible})")


class Tray(QSystemTrayIcon):
    def __init__(
        self, icon_path, preview: Preview, settings: Settings, on_quit, on_restart
    ) -> None:
        icon = QIcon(str(icon_path))
        if not icon:
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(200, 0, 0))
            icon = QIcon(pixmap)

        super().__init__(icon)
        self.preview = preview
        self.settings = settings
        self.setToolTip("Iris")

        self.menu = QMenu()

        self.preview_action = QAction("Preview", self.menu)
        self.preview_action.triggered.connect(self.toggle_preview)
        self.menu.addAction(self.preview_action)

        self.settings_action = QAction("Settings", self.menu)
        self.settings_action.triggered.connect(self.open_settings)
        self.menu.addAction(self.settings_action)

        self.menu.addSeparator()

        self.restart_action = QAction("Restart", self.menu)
        self.restart_action.triggered.connect(on_restart)
        self.menu.addAction(self.restart_action)

        self.quit_action = QAction("Quit", self.menu)
        self.quit_action.triggered.connect(on_quit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def toggle_preview(self) -> None:
        if self.preview.isVisible():
            self.preview.hide()
        else:
            self.preview.show()

    def open_settings(self) -> None:
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()
