"""Hermes's UI"""

import cv2
from dataclasses import fields
import numpy as np

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QPixmap
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
    QWidget,
    QMessageBox,
    QDialogButtonBox,
)

from hermes.config import (
    BASICS,
    CAMERA_INDEX,
    CHOICES,
    NO_SIGNAL_FRAME_PATH,
    PREVIEW,
    SCREEN,
    LIVE,
    Config,
    check_config,
    label_and_tip,
    limits,
    save,
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
            return int(widget.currentText())
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


# the config keeps colours the way OpenCV wants them, blue first
def list_to_color(bgr: list[int]) -> QColor:
    return QColor(bgr[2], bgr[1], bgr[0])


class ColorButton(QPushButton):
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

    def bgr(self) -> list[int]:
        return [self.color.blue(), self.color.green(), self.color.red()]

    def set_bgr(self, bgr: list[int]) -> None:
        self.color = list_to_color(bgr)
        self.refresh()


class Preview(QLabel):
    def __init__(self, shared, width: int, height: int, preview_refresh_time: int = 33) -> None:
        super().__init__()
        self.shared = shared
        self.setWindowTitle("Hermes")
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
        self.setWindowTitle("Hermes settings")
        self.widgets = {}
        self.color_buttons = {}

        forms = {"Basics": QFormLayout(), "Preview": QFormLayout(), "Advanced": QFormLayout()}

        for field in fields(Config):
            widget = make_widget(field.name, getattr(config, field.name))
            if widget is None:
                continue

            if field.name in BASICS:
                page_name = "Basics"
            elif field.name in PREVIEW:
                page_name = "Preview"
            else:
                page_name = "Advanced"

            label, tip = label_and_tip(field.name)
            text = QLabel(label)
            text.setToolTip(tip)
            widget.setToolTip(tip)
            forms[page_name].addRow(text, widget)
            self.widgets[field.name] = widget

        for state, bgr in config.state_colors.items():
            button = ColorButton(bgr)
            forms["Preview"].addRow(QLabel(state.capitalize()), button)
            self.color_buttons[state] = button

        tabs = QTabWidget()
        for page_name, form in forms.items():
            page = QWidget()
            page.setLayout(form)

            scroll = QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            tabs.addTab(scroll, page_name)

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )

        box.accepted.connect(self.save_settings)
        box.rejected.connect(self.close)
        restore = box.button(QDialogButtonBox.StandardButton.RestoreDefaults)
        restore.clicked.connect(self.restore_defaults)

        outer = QVBoxLayout()
        outer.addWidget(tabs)
        outer.addWidget(box)
        self.setLayout(outer)

    def fill_widgets(self, config: Config) -> None:
        for name, widget in self.widgets.items():
            write_widget(name, widget, getattr(config, name))

        for state, button in self.color_buttons.items():
            colour = config.state_colors.get(state)
            if colour is not None:
                button.set_bgr(colour)

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

        errors = check_config(self.config)
        if errors:
            errors = "\n".join(errors)
            QMessageBox.warning(self, "Failed to save some options", errors)
            return

        save(self.config)
        self.close()

        if restart_on_save:
            self.on_restart()

    def restore_defaults(self) -> None:
        self.fill_widgets(Config())


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
        self.setToolTip("Hermes")

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
