"""
Logging configuration for iMessage Analysis.

Sets up logging with appropriate format and levels.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO, format_string: Optional[str] = None, log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (default: INFO).
        format_string: Optional custom format string.
        log_file: Optional file path to write logs to.
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level, format=format_string, handlers=handlers, datefmt="%Y-%m-%d %H:%M:%S"
    )
