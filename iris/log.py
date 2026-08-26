"""Where things go wrong: one file, in the config folder."""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from iris.config import CONFIG_DIR, LOG_FILE

_previous_hook = sys.excepthook


def _log_main_thread(exc_type, exc_value, exc_traceback) -> None:
    logging.critical("crash", exc_info=(exc_type, exc_value, exc_traceback))
    _previous_hook(exc_type, exc_value, exc_traceback)


def _log_other_thread(args) -> None:
    thread = args.thread.name if args.thread is not None else "unknown"
    logging.critical(
        "crash in %s",
        thread,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def setup() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=512_000, backupCount=2, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(threadName)s: %(message)s")
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    sys.excepthook = _log_main_thread
    threading.excepthook = _log_other_thread
