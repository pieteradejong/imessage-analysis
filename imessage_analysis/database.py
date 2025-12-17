"""
Database connection and query module.

Provides database connection management and metadata query functions.
"""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import List, Tuple, Optional, Any
import logging

from imessage_analysis.config import Config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager for iMessage chat.db.

    Provides read-only access to the SQLite database with proper
    connection management and error handling.
    """

    def __init__(self, config: Config, *, use_memory: bool = False):
        """
        Initialize database connection.

        Args:
            config: Configuration object with database path.

        Raises:
            ValueError: If database path is not configured or invalid.
            sqlite3.Error: If database connection fails.
        """
        if not config.validate():
            raise ValueError(f"Database file not found or not readable: {config.db_path_str}")

        self.config = config
        self.use_memory = use_memory
        self._connection: Optional[sqlite3.Connection] = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def connect(self) -> sqlite3.Connection:
        """
        Establish read-only connection to database.

        Returns:
            SQLite connection object.

        Raises:
            sqlite3.Error: If connection fails.
        """
        if self._connection is not None:
            return self._connection

        db_path = self.config.db_path_str
        if not db_path:
            raise ValueError("Database path not configured")

        try:
            # Open in read-only mode using URI
            uri = f"file:{db_path}?mode=ro"

            if not self.use_memory:
                self._connection = sqlite3.connect(uri, uri=True)
                logger.info(f"Connected to database: {db_path}")
                return self._connection

            # Load into an in-memory database for faster reads.
            # We keep this consistent by using SQLite's backup API.
            with closing(sqlite3.connect(uri, uri=True)) as disk_conn:
                mem_conn = sqlite3.connect(":memory:")
                disk_conn.backup(mem_conn)
                self._connection = mem_conn

            logger.info(f"Loaded database into memory from: {db_path}")
            return self._connection
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Get database connection.

        Returns:
            SQLite connection object.

        Raises:
            RuntimeError: If connection not established.
        """
        if self._connection is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        return self._connection

    def _require_table_exists(self, table_name: str) -> str:
        """
        Validate a table name before interpolating into SQL.

        SQLite does not support binding identifiers, so we only allow table names
        that exist in sqlite_master.
        """
        if table_name not in self.get_table_names():
            raise ValueError(f"Unknown table name: {table_name!r}")
        return table_name

    def get_table_names(self) -> List[str]:
        """
        Get all table names in the database.

        Returns:
            List of table names.
        """
        query = "SELECT `name` FROM `sqlite_master` WHERE `type`='table';"
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            return [row[0] for row in results]

    def get_columns_for_table(
        self, table_name: str
    ) -> List[Tuple[str, str, int, Optional[str], Optional[int], int]]:
        """
        Get column information for a table.

        Args:
            table_name: Name of the table.

        Returns:
            List of column information tuples (name, type, notnull, default, pk).
        """
        safe_table = self._require_table_exists(table_name)
        query = f"PRAGMA table_info('{safe_table}');"
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table.

        Returns:
            Number of rows in the table.
        """
        safe_table = self._require_table_exists(table_name)
        query = f"SELECT COUNT(*) FROM `{safe_table}`;"
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_row_counts_by_table(
        self, table_names: Optional[List[str]] = None
    ) -> List[Tuple[str, int]]:
        """
        Get row counts for multiple tables.

        Args:
            table_names: Optional list of table names. If None, uses all tables.

        Returns:
            List of (table_name, row_count) tuples.
        """
        if table_names is None:
            table_names = self.get_table_names()

        return [(table_name, self.get_row_count(table_name)) for table_name in table_names]

    def get_table_creation_query(self, table_name: str) -> Optional[str]:
        """
        Get the CREATE TABLE query for a table.

        Args:
            table_name: Name of the table.

        Returns:
            CREATE TABLE SQL statement, or None if not found.
        """
        query = "SELECT `sql` FROM sqlite_master WHERE `tbl_name`=? AND `type`='table';"
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(query, (table_name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def execute_query(
        self, query: str, parameters: Optional[Tuple[Any, ...]] = None
    ) -> List[Tuple[Any, ...]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query string.
            parameters: Optional query parameters.

        Returns:
            List of result rows.
        """
        with closing(self.connection.cursor()) as cursor:
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            return cursor.fetchall()
