"""
Logging configuration for iMessage Analysis.

Sets up logging with appropriate format and levels using dictConfig
for robust configuration that supports environment-based log levels.

Environment Variables:
    LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO if not set or invalid.

Usage:
    from imessage_analysis.logger_config import setup_logging
    setup_logging()  # Uses LOG_LEVEL env var, defaults to INFO

    # Or override explicitly:
    setup_logging(level=logging.DEBUG)
"""

import logging
import logging.config
import os
import sys
from typing import Optional


def get_log_level() -> int:
    """
    Get log level from LOG_LEVEL environment variable.

    Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive).
    Defaults to INFO if not set or invalid.

    Returns:
        Logging level constant (e.g., logging.INFO).
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, None)

    if level is None or not isinstance(level, int):
        # Invalid level name, fall back to INFO
        return logging.INFO

    return level


def setup_logging(
    level: Optional[int] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the application using dictConfig.

    This function can be called multiple times safely. It uses dictConfig
    which properly reconfigures logging (unlike basicConfig which only
    works once).

    Args:
        level: Logging level. If None, reads from LOG_LEVEL env var (default: INFO).
        format_string: Optional custom format string.
        log_file: Optional file path to write logs to (with rotation).
    """
    if level is None:
        level = get_log_level()

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Build configuration dictionary
    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,  # Don't clobber existing loggers
        "formatters": {
            "standard": {
                "format": format_string,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    # Add rotating file handler if log_file specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "standard",
            "filename": log_file,
            "maxBytes": 10_485_760,  # 10 MB
            "backupCount": 5,
        }
        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)
