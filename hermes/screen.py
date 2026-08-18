"""Where the monitors are. Windows only."""

import ctypes
from ctypes import wintypes

from hermes.geometry import Rect

PRIMARY = "Primary"
ALL = "All"

# GetSystemMetrics indices
CX_SCREEN, CY_SCREEN = 0, 1
X_VIRTUAL, Y_VIRTUAL, CX_VIRTUAL, CY_VIRTUAL = 76, 77, 78, 79

_ENUM_PROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM,
)


def _metric(index: int) -> int:
    return ctypes.windll.user32.GetSystemMetrics(index)


# the primary monitor is what defines the origin of the desktop
def primary() -> Rect:
    return Rect(0, 0, _metric(CX_SCREEN), _metric(CY_SCREEN))


# the box around every monitor. Its corner is negative as soon as one of them
# sits left of or above the primary
def virtual() -> Rect:
    return Rect(
        _metric(X_VIRTUAL), _metric(Y_VIRTUAL), _metric(CX_VIRTUAL), _metric(CY_VIRTUAL)
    )


def monitors() -> list[Rect]:
    found: list[Rect] = []

    # Windows calls this once per monitor; anything other than zero means carry on
    def collect(monitor, device_context, rect_pointer, data) -> int:
        edges = rect_pointer.contents
        found.append(
            Rect(
                edges.left,
                edges.top,
                edges.right - edges.left,
                edges.bottom - edges.top,
            )
        )
        return 1

    ctypes.windll.user32.EnumDisplayMonitors(None, None, _ENUM_PROC(collect), 0)
    return found


# save rect for config and ui
def choices() -> list[str]:
    names = [PRIMARY, ALL]
    for number, rect in enumerate(monitors(), start=1):
        names.append(f"{number}: {rect.width}x{rect.height} at {rect.x},{rect.y}")
    return names


# load rect
def rect_for(name: str) -> Rect:
    if name == ALL:
        return virtual()

    number, _, _ = name.partition(":")
    try:
        wanted = int(number)
    except ValueError:
        return primary()

    found = monitors()
    if 1 <= wanted <= len(found):
        return found[wanted - 1]

    return primary()
