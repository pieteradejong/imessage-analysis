"""
Configuration module for iMessage Analysis project.

Handles configuration settings including database file paths.

Database Paths:
    - chat.db: Apple's iMessage database (read-only source)
    - analysis.db: Our analytical database (read-write target)
    - AddressBook: Apple's Contacts database (read-only, optional)

See DATA_ARCHITECTURE.md for the full data architecture.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class for iMessage Analysis."""

    # Default database file name
    DEFAULT_DB_NAME = "chat.db"

    # Default path to Messages directory on macOS
    DEFAULT_MESSAGES_PATH = Path.home() / "Library" / "Messages"

    # Default path for analysis.db (our database)
    DEFAULT_ANALYSIS_PATH = Path.home() / ".imessage_analysis"
    DEFAULT_ANALYSIS_DB_NAME = "analysis.db"

    # Default path to Contacts database on macOS
    DEFAULT_CONTACTS_PATH = Path.home() / "Library" / "Application Support" / "AddressBook"

    def __init__(
        self,
        db_path: Optional[str] = None,
        analysis_db_path: Optional[str] = None,
        contacts_db_path: Optional[str] = None,
    ):
        """
        Initialize configuration.

        Args:
            db_path: Optional path to chat.db file. If not provided, will look
                    in current directory, then in default Messages directory.
            analysis_db_path: Optional path to analysis.db file. If not provided,
                    defaults to ~/.imessage_analysis/analysis.db
            contacts_db_path: Optional path to AddressBook database. If not provided,
                    will attempt to find it in the default location.
        """
        # Chat.db path (source)
        self._db_path: Optional[Path] = None
        if db_path:
            self._db_path = Path(db_path)
        else:
            # Try current directory first
            current_dir_db = Path.cwd() / self.DEFAULT_DB_NAME
            if current_dir_db.exists():
                self._db_path = current_dir_db
            # Then try default Messages directory
            elif (self.DEFAULT_MESSAGES_PATH / self.DEFAULT_DB_NAME).exists():
                self._db_path = self.DEFAULT_MESSAGES_PATH / self.DEFAULT_DB_NAME

        # Analysis.db path (our database)
        self._analysis_db_path: Path
        if analysis_db_path:
            self._analysis_db_path = Path(analysis_db_path)
        else:
            self._analysis_db_path = self.DEFAULT_ANALYSIS_PATH / self.DEFAULT_ANALYSIS_DB_NAME

        # Contacts.db path (optional)
        self._contacts_db_path: Optional[Path] = None
        if contacts_db_path:
            self._contacts_db_path = Path(contacts_db_path)
        else:
            # Try to find AddressBook database
            self._contacts_db_path = self._find_contacts_db()

    def _find_contacts_db(self) -> Optional[Path]:
        """
        Find the AddressBook database file.

        The AddressBook database has a versioned filename like:
        AddressBook-v22.abcddb

        Returns:
            Path to the Contacts database, or None if not found.
        """
        if not self.DEFAULT_CONTACTS_PATH.exists():
            return None

        # Look for AddressBook-vXX.abcddb files
        for f in self.DEFAULT_CONTACTS_PATH.iterdir():
            if f.name.startswith("AddressBook-v") and f.name.endswith(".abcddb"):
                return f

        return None

    @property
    def db_path(self) -> Optional[Path]:
        """Get the chat.db file path (source database)."""
        return self._db_path

    @property
    def db_path_str(self) -> Optional[str]:
        """Get the chat.db file path as a string."""
        return str(self._db_path) if self._db_path else None

    @property
    def analysis_db_path(self) -> Path:
        """Get the analysis.db file path (our database)."""
        return self._analysis_db_path

    @property
    def analysis_db_path_str(self) -> str:
        """Get the analysis.db file path as a string."""
        return str(self._analysis_db_path)

    @property
    def contacts_db_path(self) -> Optional[Path]:
        """Get the Contacts database file path (optional)."""
        return self._contacts_db_path

    @property
    def contacts_db_path_str(self) -> Optional[str]:
        """Get the Contacts database file path as a string."""
        return str(self._contacts_db_path) if self._contacts_db_path else None

    def validate(self) -> bool:
        """
        Validate that the chat.db file exists and is readable.

        Returns:
            True if chat.db exists and is readable, False otherwise.
        """
        if not self._db_path:
            return False
        return self._db_path.exists() and os.access(self._db_path, os.R_OK)

    def validate_contacts(self) -> bool:
        """
        Validate that the Contacts database exists and is readable.

        Returns:
            True if Contacts database exists and is readable, False otherwise.
        """
        if not self._contacts_db_path:
            return False
        return self._contacts_db_path.exists() and os.access(self._contacts_db_path, os.R_OK)

    def ensure_analysis_dir(self) -> None:
        """
        Ensure the analysis.db parent directory exists.

        Creates the directory if it doesn't exist.
        """
        self._analysis_db_path.parent.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[Config] = None


def get_config(db_path: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance.

    Args:
        db_path: Optional path to chat.db file.

    Returns:
        Config instance.
    """
    global _config
    if _config is None or db_path is not None:
        _config = Config(db_path)
    return _config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.

    Args:
        config: Config instance to use.
    """
    global _config
    _config = config
