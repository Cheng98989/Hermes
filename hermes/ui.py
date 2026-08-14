"""Hermes's UI"""

from dataclasses import fields

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from hermes.config import BASICS, PREVIEW, ROOT, Config, label_and_tip, save

ICON_PATH = ROOT / "assets" / "icon.png"




def make_widget(value):
    if isinstance(value, bool):
        widget = QCheckBox()
        widget.setChecked(value)
        return widget

    if isinstance(value, int):
        widget = QSpinBox()
        widget.setRange(0, 100)
        widget.setValue(value)
        return widget

    if isinstance(value, float):
        widget = QDoubleSpinBox()
        widget.setRange(0.0, 100.0)
        widget.setDecimals(3)
        widget.setSingleStep(0.01)
        widget.setValue(value)
        return widget

    if isinstance(value, str):
        widget = QComboBox()
        widget.addItems(["Right", "Left"])
        widget.setCurrentText(value)
        return widget

    return None


def read_widget(widget):
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, QComboBox):
        return widget.currentText()

    return widget.value()


class ColorButton(QPushButton):
    def __init__(self, bgr: list[int]) -> None:
        super().__init__()
        self.color = QColor(bgr[2], bgr[1], bgr[0])
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


class Preview(QLabel):
    def __init__(self, shared, width: int, height: int, preview_refresh_time: int = 33) -> None:
        super().__init__()
        self.shared = shared
        self.setWindowTitle("Hermes")
        self.resize(width, height)
        self.setScaledContents(True)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(preview_refresh_time)

    def refresh(self) -> None:
        frame = self.shared.frame
        if frame is None:
            return

        height, width = frame.shape[:2]
        image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888)
        self.setPixmap(QPixmap.fromImage(image))


class Settings(QDialog):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle("Hermes settings")
        self.widgets = {}
        self.color_buttons = {}

        forms = {"Basics": QFormLayout(), "Preview": QFormLayout(), "Advanced": QFormLayout()}

        for field in fields(Config):
            widget = make_widget(getattr(config, field.name))
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
            tabs.addTab(page, page_name)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)

        outer = QVBoxLayout()
        outer.addWidget(tabs)
        outer.addWidget(QLabel("Changes apply on restart"))
        outer.addWidget(save_button)
        self.setLayout(outer)

    def save_settings(self) -> None:
        for name, widget in self.widgets.items():
            setattr(self.config, name, read_widget(widget))

        for state, button in self.color_buttons.items():
            self.config.state_colors[state] = button.bgr()

        save(self.config)
        self.close()


class Tray(QSystemTrayIcon):
    def __init__(self, icon_path, preview: Preview, settings: Settings, on_quit) -> None:
        super().__init__(QIcon(str(icon_path)))
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
