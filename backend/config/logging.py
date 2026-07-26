"""
logging.py — structured logging setup for the SellerOS backend.

Replaces bare `print()` calls (main.py's startup message, init_db's
"Database initialized successfully.") with proper `logging` calls that
carry a level, a timestamp, and a logger name — so in production these
can be filtered, shipped to a log aggregator, or silenced by level
without touching call sites, none of which is possible with print().

Usage:
    from backend.config.logging import configure_logging
    configure_logging()  # call once, at process startup, before
                          # anything else logs
"""
from __future__ import annotations

import logging
import sys

from backend.config.settings import settings

_CONFIGURED = False


def configure_logging() -> None:
    """
    Configure the root logger once. Safe to call more than once —
    subsequent calls are no-ops, so importing this in multiple places
    (main.py, a future worker process, tests) never double-registers
    handlers or duplicates log lines.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers if uvicorn's --reload re-imports this
    # module in the same process.
    root.handlers = [handler]

    # uvicorn/fastapi's own loggers are noisy at DEBUG; leave them at
    # their own default unless the app itself is in DEBUG mode.
    logging.getLogger("uvicorn.access").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper so call sites don't need to import
    `logging` directly: `log = get_logger(__name__)`."""
    return logging.getLogger(name)
