"""Moving the real mouse pointer."""

import ctypes

from pynput.mouse import Button, Controller

# Only the middle of the frame maps to the screen. The corners of the camera's
# view are neither comfortable to reach nor well tracked, and the anchor sits
# inside the hand - so pushing it all the way to the edge takes the fingers
# out of frame entirely, which loses the pinch.
#
# Narrower zone: smaller movements cover the screen, less precision.
# Wider zone: more precision, but the hand has to travel further.
ZONE_MIN = 0.25
ZONE_MAX = 0.75

def screen_size() -> tuple[int, int]:
    """Size of the primary monitor in pixels.

    Windows-only, and kept in a function on purpose: ctypes.windll does not
    exist elsewhere, so at module level this would stop the whole app from
    starting on another platform rather than only the part that needs it.

    The primary monitor, not the whole desktop - this machine spans two
    screens, and mapping a hand across both would make every movement twice
    as coarse.
    """
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))


def _zone_fraction(value: float) -> float:
    """Where `value` falls inside the active zone, 0 to 1, clamped."""
    return min(max((value - ZONE_MIN)/(ZONE_MAX - ZONE_MIN), 0.0), 1.0)

def to_screen(x: float, y: float, screen_width: int, screen_height: int) -> tuple[int, int]:
    """Map a point inside the active zone onto the whole screen."""
    pixel_x = _zone_fraction(x) * screen_width
    pixel_y = _zone_fraction(y) * screen_height
    return (int(pixel_x),int(pixel_y))

class Cursor:
    """The mouse: where it points, and whether its button is down.

    Takes plain numbers, not landmarks - deciding which point of the hand
    drives the pointer is the caller's business, and swapping that choice
    should not touch this file.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self._mouse = Controller()
        self.screen_size = (screen_width, screen_height)
        self._pressed = False

    def move_to_pixels(self, x: float, y: float) -> tuple[int, int]:
        """Move the pointer to a point already in screen pixels.

        Separate from move_to so a caller can put something between the
        mapping and the mouse - the dead zone has to work in pixels, because
        that is the unit a tremor is judged in.
        """
        position = (int(x), int(y))
        self._mouse.position = position
        return position

    def move_to(self, x: float, y: float) -> tuple[int, int]:
        """Move the pointer. x and y are 0..1 across the camera frame."""
        return self.move_to_pixels(*to_screen(x, y, *self.screen_size))

    def set_pressed(self, pressed: bool) -> None:
        """Hold or release the left button.

        Safe to call every frame with the same value: only a change reaches
        the operating system. Describing the state rather than the transition
        means the caller needs no memory of its own - and cannot press the
        button thirty times a second by mistake.
        """
        if pressed == self._pressed:
            return

        if pressed:
            self._mouse.press(Button.left)
        else:
            self._mouse.release(Button.left)

        self._pressed = pressed
        
    def scroll(self, clicks: int) -> None:
        """Scroll by whole clicks; positive is up.

        Zero is dropped rather than sent. Most frames produce no click at all,
        and pynput would otherwise push an event to the operating system
        thirty times a second to say that nothing happened.
        """
        if clicks:
            self._mouse.scroll(0, clicks)
        
