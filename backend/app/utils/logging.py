"""
Structured logging configuration — Windows-safe (no emoji in stream handler).
"""
import logging
import sys
from functools import lru_cache


@lru_cache(maxsize=None)
def _get_settings():
    from app.config import get_settings
    return get_settings()


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that is safe to use on Windows terminals (cp1252).
    Emoji and non-ASCII characters in messages are silently replaced with '?'
    so the logging system never raises UnicodeEncodeError.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Use a stream handler that encodes safely
        stream = open(
            sys.stdout.fileno(),
            mode="w",
            encoding=sys.stdout.encoding or "utf-8",
            errors="replace",   # <-- replaces unencodable chars with '?'
            closefd=False,
            buffering=1,
        )
        handler = logging.StreamHandler(stream)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        settings = _get_settings()
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger


def silence_sqlalchemy_logs():
    """
    Suppress verbose SQLAlchemy SQL echo from filling the console.
    Call this once from app startup.
    """
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
