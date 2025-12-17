"""
Configuration module for iMessage Analysis project.

Handles configuration settings including database file paths.
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
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            db_path: Optional path to chat.db file. If not provided, will look
                    in current directory, then in default Messages directory.
        """
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
    
    @property
    def db_path(self) -> Optional[Path]:
        """Get the database file path."""
        return self._db_path
    
    @property
    def db_path_str(self) -> Optional[str]:
        """Get the database file path as a string."""
        return str(self._db_path) if self._db_path else None
    
    def validate(self) -> bool:
        """
        Validate that the database file exists and is readable.
        
        Returns:
            True if database file exists and is readable, False otherwise.
        """
        if not self._db_path:
            return False
        return self._db_path.exists() and os.access(self._db_path, os.R_OK)


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


