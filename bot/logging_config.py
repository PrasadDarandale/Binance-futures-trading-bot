"""
Logging configuration for the trading bot.
Logs to both console (INFO+) and a rotating file (DEBUG+).
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "trading_bot.log"

MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level_console: str = "INFO", log_level_file: str = "DEBUG") -> None:
    """
    Configure root logger with:
    - RotatingFileHandler  → logs/trading_bot.log  (DEBUG by default)
    - StreamHandler (stdout) → console              (INFO by default)
    """
    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(getattr(logging, log_level_file.upper(), logging.DEBUG))
    fh.setFormatter(formatter)


    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level_console.upper(), logging.INFO))
    ch.setFormatter(formatter)


    if not root.handlers:
        root.addHandler(fh)
        root.addHandler(ch)
    else:
        root.handlers.clear()
        root.addHandler(fh)
        root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (call setup_logging first)."""
    return logging.getLogger(name)
