"""
iMessage Analysis - A tool for analyzing iMessage data from macOS chat.db.

This package provides functionality to:
- Connect to and query the iMessage database
- Analyze message patterns and statistics
- Visualize message data
"""

__version__ = "0.1.0"

from imessage_analysis.config import get_config, Config
from imessage_analysis.database import DatabaseConnection

__all__ = [
    "get_config",
    "Config",
    "DatabaseConnection",
]
