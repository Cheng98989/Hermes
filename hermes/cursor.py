"""Moving the real mouse pointer. Windows only."""

import ctypes

from pynput.mouse import Button, Controller

from hermes.geometry import Point


# the primary monitor, not the whole desktop. In a function because
# ctypes.windll does not exist on other platforms
def screen_size() -> tuple[int, int]:
    user32 = ctypes.windll.user32
    return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))


# where `value` falls inside the active zone, 0 to 1, clamped
def _zone_fraction(value: float, zone_min: float, zone_max: float) -> float:
    return min(max((value - zone_min) / (zone_max - zone_min), 0.0), 1.0)

# a point in the frame -> a pixel on the monitor, kept in floats: rounding
# to whole pixels happens once, at the mouse
def to_screen(
    point: Point,
    screen_width: int,
    screen_height: int,
    zone_min: float,
    zone_max: float,
) -> Point:
    return Point(
        _zone_fraction(point.x, zone_min, zone_max) * screen_width,
        _zone_fraction(point.y, zone_min, zone_max) * screen_height,
    )


# takes points, not landmarks: which point of the hand drives the pointer is
# decided by the caller
class Cursor:
    def __init__(self, screen_width: int, screen_height: int) -> None:
        self._mouse = Controller()
        self.screen_size = (screen_width, screen_height)
        self._pressed = False

    # takes a point already in screen pixels: the caller maps it, so that the
    # dead zone can sit between the mapping and the mouse
    def move_to_pixels(self, point: Point) -> Point:
        position = Point(int(point.x), int(point.y))
        self._mouse.position = int(position.x), int(position.y)
        return position

    # safe to call every frame: only a change reaches the operating system
    def set_pressed(self, pressed: bool) -> None:
        if pressed == self._pressed:
            return

        if pressed:
            self._mouse.press(Button.left)
        else:
            self._mouse.release(Button.left)

        self._pressed = pressed

    # positive is up. Zero is dropped: most frames produce no click at all
    def scroll(self, clicks: int) -> None:
        if clicks:
            self._mouse.scroll(0, clicks)
