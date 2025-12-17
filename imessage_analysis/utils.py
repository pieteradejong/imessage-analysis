"""
Utility functions and classes for iMessage Analysis.
"""

from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def format_timestamp(timestamp: int) -> str:
    """
    Convert iMessage timestamp to readable format.

    iMessage timestamps are in nanoseconds since 2001-01-01.

    Args:
        timestamp: iMessage timestamp in nanoseconds.

    Returns:
        Formatted date string.
    """
    import datetime

    # Convert nanoseconds to seconds and add epoch offset
    epoch_2001 = datetime.datetime(2001, 1, 1)
    seconds = timestamp / 1_000_000_000
    dt = epoch_2001 + datetime.timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_message_count(count: int) -> str:
    """
    Format message count with appropriate units.

    Args:
        count: Number of messages.

    Returns:
        Formatted string (e.g., "1,234" or "1.2K").
    """
    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"
