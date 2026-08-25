"""Moving the real mouse pointer. Windows only."""

from pynput.mouse import Button, Controller

from iris.geometry import Point, Rect


# where `value` falls inside the active zone, 0 to 1, clamped
def _zone_fraction(value: float, zone_min: float, zone_max: float) -> float:
    return min(max((value - zone_min) / (zone_max - zone_min), 0.0), 1.0)


def to_screen(point: Point, screen: Rect, zone_min: float, zone_max: float) -> Point:
    return Point(
        screen.x + _zone_fraction(point.x, zone_min, zone_max) * screen.width,
        screen.y + _zone_fraction(point.y, zone_min, zone_max) * screen.height,
    )


# takes points, not landmarks: which point of the hand drives the pointer is
# decided by the caller
class Cursor:
    def __init__(self) -> None:
        self._mouse = Controller()
        self._pressed = False

    # takes a point already in screen pixels: the caller maps it, so that the
    # dead zone can sit between the mapping and the mouse. Rounded rather than
    def move_to_pixels(self, point: Point) -> Point:
        position = Point(round(point.x), round(point.y))
        self._mouse.position = (int(position.x), int(position.y))
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

    # press and release in one go, fire is decided by RightClickTracker
    def right_click(self) -> None:
        self._mouse.click(Button.right)

    # positive is up. Zero is dropped: most frames produce no click at all
    def scroll(self, clicks: int) -> None:
        if clicks:
            self._mouse.scroll(0, clicks)
