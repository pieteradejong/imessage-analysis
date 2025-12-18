"""
Tests for database.py DatabaseConnection class.

Tests database connection management and query execution.
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from imessage_analysis.config import Config
from imessage_analysis.database import DatabaseConnection


@pytest.fixture
def sample_db(tmp_path: Path) -> Path:
    """Create a sample SQLite database for testing."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE message (
                rowid INTEGER PRIMARY KEY,
                text TEXT,
                date INTEGER
            );
            
            CREATE TABLE chat (
                rowid INTEGER PRIMARY KEY,
                chat_identifier TEXT
            );
            
            INSERT INTO message (rowid, text, date) VALUES 
                (1, 'Hello', 1000000000),
                (2, 'World', 2000000000);
            
            INSERT INTO chat (rowid, chat_identifier) VALUES 
                (1, '+14155551234');
        """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


@pytest.fixture
def mock_config(sample_db: Path):
    """Create a mock config with the sample database path."""
    config = MagicMock(spec=Config)
    config.db_path_str = str(sample_db)
    config.validate.return_value = True
    return config


class TestDatabaseConnectionInit:
    """Tests for DatabaseConnection initialization."""

    def test_init_with_valid_config(self, mock_config):
        """Should initialize with valid config."""
        db = DatabaseConnection(mock_config)
        assert db.config == mock_config
        assert db._connection is None

    def test_init_with_invalid_config(self):
        """Should raise ValueError with invalid config."""
        config = MagicMock(spec=Config)
        config.validate.return_value = False
        config.db_path_str = "/invalid/path"

        with pytest.raises(ValueError) as exc_info:
            DatabaseConnection(config)
        assert "not found or not readable" in str(exc_info.value)

    def test_init_use_memory_flag(self, mock_config):
        """Should store use_memory flag."""
        db = DatabaseConnection(mock_config, use_memory=True)
        assert db.use_memory is True

        db2 = DatabaseConnection(mock_config, use_memory=False)
        assert db2.use_memory is False


class TestDatabaseConnectionConnect:
    """Tests for connect method."""

    def test_connect_creates_connection(self, mock_config):
        """Should create a connection."""
        db = DatabaseConnection(mock_config)
        conn = db.connect()

        assert conn is not None
        assert db._connection is not None
        db.close()

    def test_connect_returns_same_connection(self, mock_config):
        """Multiple connect calls should return same connection."""
        db = DatabaseConnection(mock_config)
        conn1 = db.connect()
        conn2 = db.connect()

        assert conn1 is conn2
        db.close()

    def test_connect_with_use_memory(self, mock_config):
        """Should load database into memory when use_memory=True."""
        db = DatabaseConnection(mock_config, use_memory=True)
        conn = db.connect()

        # Should still work - connection is to in-memory database
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM message")
        count = cursor.fetchone()[0]
        assert count == 2  # We inserted 2 messages
        db.close()


class TestDatabaseConnectionClose:
    """Tests for close method."""

    def test_close_disconnects(self, mock_config):
        """Should close the connection."""
        db = DatabaseConnection(mock_config)
        db.connect()
        db.close()

        assert db._connection is None

    def test_close_without_connection(self, mock_config):
        """Should handle close without prior connect."""
        db = DatabaseConnection(mock_config)
        # Should not raise
        db.close()
        assert db._connection is None

    def test_double_close(self, mock_config):
        """Should handle double close gracefully."""
        db = DatabaseConnection(mock_config)
        db.connect()
        db.close()
        db.close()  # Should not raise
        assert db._connection is None


class TestDatabaseConnectionContextManager:
    """Tests for context manager protocol."""

    def test_context_manager_connects(self, mock_config):
        """Context manager should connect on entry."""
        with DatabaseConnection(mock_config) as db:
            assert db._connection is not None

    def test_context_manager_closes(self, mock_config):
        """Context manager should close on exit."""
        db = DatabaseConnection(mock_config)
        with db:
            pass
        assert db._connection is None


class TestDatabaseConnectionProperty:
    """Tests for connection property."""

    def test_connection_property_returns_connection(self, mock_config):
        """Property should return active connection."""
        db = DatabaseConnection(mock_config)
        db.connect()
        conn = db.connection
        assert conn is db._connection
        db.close()

    def test_connection_property_raises_without_connect(self, mock_config):
        """Property should raise if not connected."""
        db = DatabaseConnection(mock_config)
        with pytest.raises(RuntimeError) as exc_info:
            _ = db.connection
        assert "not established" in str(exc_info.value)


class TestGetTableNames:
    """Tests for get_table_names method."""

    def test_returns_table_names(self, mock_config):
        """Should return list of table names."""
        with DatabaseConnection(mock_config) as db:
            tables = db.get_table_names()

        assert isinstance(tables, list)
        assert "message" in tables
        assert "chat" in tables

    def test_returns_list(self, mock_config):
        """Should return a list even if empty."""
        with DatabaseConnection(mock_config) as db:
            tables = db.get_table_names()
        assert isinstance(tables, list)


class TestGetColumnsForTable:
    """Tests for get_columns_for_table method."""

    def test_returns_column_info(self, mock_config):
        """Should return column information for table."""
        with DatabaseConnection(mock_config) as db:
            columns = db.get_columns_for_table("message")

        assert len(columns) == 3  # rowid, text, date

    def test_invalid_table_raises(self, mock_config):
        """Should raise ValueError for invalid table."""
        with DatabaseConnection(mock_config) as db:
            with pytest.raises(ValueError) as exc_info:
                db.get_columns_for_table("nonexistent_table")
            assert "Unknown table" in str(exc_info.value)


class TestGetRowCount:
    """Tests for get_row_count method."""

    def test_returns_count(self, mock_config):
        """Should return row count for table."""
        with DatabaseConnection(mock_config) as db:
            count = db.get_row_count("message")
        assert count == 2

    def test_invalid_table_raises(self, mock_config):
        """Should raise ValueError for invalid table."""
        with DatabaseConnection(mock_config) as db:
            with pytest.raises(ValueError):
                db.get_row_count("nonexistent_table")


class TestGetRowCountsByTable:
    """Tests for get_row_counts_by_table method."""

    def test_returns_counts_for_all_tables(self, mock_config):
        """Should return counts for all tables."""
        with DatabaseConnection(mock_config) as db:
            counts = db.get_row_counts_by_table()

        # Convert to dict for easier testing
        counts_dict = dict(counts)
        assert "message" in counts_dict
        assert "chat" in counts_dict
        assert counts_dict["message"] == 2
        assert counts_dict["chat"] == 1

    def test_returns_counts_for_specific_tables(self, mock_config):
        """Should return counts only for specified tables."""
        with DatabaseConnection(mock_config) as db:
            counts = db.get_row_counts_by_table(["message"])

        assert len(counts) == 1
        assert counts[0][0] == "message"
        assert counts[0][1] == 2


class TestGetTableCreationQuery:
    """Tests for get_table_creation_query method."""

    def test_returns_create_statement(self, mock_config):
        """Should return CREATE TABLE statement."""
        with DatabaseConnection(mock_config) as db:
            sql = db.get_table_creation_query("message")

        assert sql is not None
        assert "CREATE TABLE" in sql
        assert "message" in sql

    def test_nonexistent_table_returns_none(self, mock_config):
        """Should return None for nonexistent table."""
        with DatabaseConnection(mock_config) as db:
            sql = db.get_table_creation_query("nonexistent")
        assert sql is None


class TestExecuteQuery:
    """Tests for execute_query method."""

    def test_execute_simple_query(self, mock_config):
        """Should execute simple SELECT query."""
        with DatabaseConnection(mock_config) as db:
            results = db.execute_query("SELECT * FROM message")

        assert len(results) == 2

    def test_execute_with_parameters(self, mock_config):
        """Should execute parameterized query."""
        with DatabaseConnection(mock_config) as db:
            results = db.execute_query("SELECT * FROM message WHERE rowid = ?", (1,))

        assert len(results) == 1
        assert results[0][1] == "Hello"

    def test_execute_returns_list(self, mock_config):
        """Should return list of tuples."""
        with DatabaseConnection(mock_config) as db:
            results = db.execute_query("SELECT * FROM message")

        assert isinstance(results, list)
        assert all(isinstance(row, tuple) for row in results)

    def test_execute_empty_result(self, mock_config):
        """Should return empty list for no results."""
        with DatabaseConnection(mock_config) as db:
            results = db.execute_query("SELECT * FROM message WHERE rowid = ?", (999,))

        assert results == []
