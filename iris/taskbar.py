"""Telling the desktop who we are. A no-op anywhere but Windows."""

import ctypes
import sys


# Declare if in windows the process ID
def claim_identity(app_id: str) -> None:
    if sys.platform != "win32":
        return

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
