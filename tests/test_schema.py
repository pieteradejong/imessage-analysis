"""
Tests for ETL schema module.

Tests schema creation, table existence, constraints, and indexes.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.schema import (
    create_schema,
    get_table_names,
    verify_schema,
    SCHEMA_VERSION,
)


class TestCreateSchema:
    """Tests for schema creation."""

    def test_creates_database_file(self, tmp_path: Path):
        """Schema creation should create the database file."""
        db_path = tmp_path / "test.db"
        assert not db_path.exists()

        create_schema(db_path)

        assert db_path.exists()

    def test_creates_parent_directory(self, tmp_path: Path):
        """Schema creation should create parent directories if needed."""
        db_path = tmp_path / "subdir" / "nested" / "test.db"
        assert not db_path.parent.exists()

        create_schema(db_path)

        assert db_path.exists()
        assert db_path.parent.exists()

    def test_idempotent(self, tmp_path: Path):
        """Schema creation should be idempotent (safe to run multiple times)."""
        db_path = tmp_path / "test.db"

        # Create schema twice
        create_schema(db_path)
        create_schema(db_path)  # Should not raise

        # Verify tables exist
        assert verify_schema(db_path)

    def test_creates_all_required_tables(self, empty_analysis_db: Path):
        """Schema should create all required tables."""
        tables = get_table_names(empty_analysis_db)

        required = ["dim_person", "dim_contact_method", "dim_handle", "fact_message", "etl_state"]
        for table in required:
            assert table in tables, f"Missing table: {table}"


class TestGetTableNames:
    """Tests for get_table_names function."""

    def test_returns_list_of_tables(self, empty_analysis_db: Path):
        """Should return a list of table names."""
        tables = get_table_names(empty_analysis_db)

        assert isinstance(tables, list)
        assert len(tables) >= 5  # At least our 5 tables

    def test_empty_database(self, tmp_path: Path):
        """Empty database should return empty list."""
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()

        tables = get_table_names(db_path)
        assert tables == []


class TestVerifySchema:
    """Tests for verify_schema function."""

    def test_valid_schema_returns_true(self, empty_analysis_db: Path):
        """Valid schema should return True."""
        assert verify_schema(empty_analysis_db) is True

    def test_nonexistent_file_returns_false(self, tmp_path: Path):
        """Non-existent file should return False."""
        db_path = tmp_path / "nonexistent.db"
        assert verify_schema(db_path) is False

    def test_incomplete_schema_returns_false(self, tmp_path: Path):
        """Database missing required tables should return False."""
        db_path = tmp_path / "incomplete.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE dim_person (id TEXT PRIMARY KEY);")
        conn.commit()
        conn.close()

        assert verify_schema(db_path) is False


class TestSchemaConstraints:
    """Tests for schema constraints and structure."""

    def test_dim_person_primary_key(self, empty_analysis_db: Path):
        """dim_person should have person_id as primary key."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert should work
            conn.execute(
                """INSERT INTO dim_person 
                   (person_id, source, created_at, updated_at) 
                   VALUES ('test-1', 'inferred', '2024-01-01', '2024-01-01')"""
            )
            conn.commit()

            # Duplicate should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO dim_person 
                       (person_id, source, created_at, updated_at) 
                       VALUES ('test-1', 'inferred', '2024-01-01', '2024-01-01')"""
                )
        finally:
            conn.close()

    def test_dim_handle_primary_key(self, empty_analysis_db: Path):
        """dim_handle should have handle_id as primary key."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            conn.execute(
                """INSERT INTO dim_handle 
                   (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at) 
                   VALUES (1, '+1234', '+1234', 'phone', '2024-01-01', '2024-01-01')"""
            )
            conn.commit()

            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO dim_handle 
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at) 
                       VALUES (1, '+5678', '+5678', 'phone', '2024-01-01', '2024-01-01')"""
                )
        finally:
            conn.close()

    def test_fact_message_primary_key(self, empty_analysis_db: Path):
        """fact_message should have message_id as primary key."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            conn.execute(
                """INSERT INTO fact_message 
                   (message_id, date_utc, is_from_me, created_at) 
                   VALUES (1, '2024-01-01T00:00:00Z', 0, '2024-01-01')"""
            )
            conn.commit()

            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO fact_message 
                       (message_id, date_utc, is_from_me, created_at) 
                       VALUES (1, '2024-01-02T00:00:00Z', 1, '2024-01-01')"""
                )
        finally:
            conn.close()

    def test_handle_type_check_constraint(self, empty_analysis_db: Path):
        """dim_handle.handle_type should only allow valid values."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Valid types should work
            for i, handle_type in enumerate(["phone", "email", "unknown"]):
                conn.execute(
                    """INSERT INTO dim_handle 
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at) 
                       VALUES (?, 'test', 'test', ?, '2024-01-01', '2024-01-01')""",
                    (i + 1, handle_type),
                )
            conn.commit()

            # Invalid type should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO dim_handle 
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at) 
                       VALUES (99, 'test', 'test', 'invalid', '2024-01-01', '2024-01-01')"""
                )
        finally:
            conn.close()

    def test_contact_method_type_check_constraint(self, empty_analysis_db: Path):
        """dim_contact_method.type should only allow 'phone' or 'email'."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Valid types should work
            conn.execute(
                """INSERT INTO dim_contact_method 
                   (method_id, type, value_raw, value_normalized, created_at) 
                   VALUES ('m1', 'phone', '+1234', '+1234', '2024-01-01')"""
            )
            conn.execute(
                """INSERT INTO dim_contact_method 
                   (method_id, type, value_raw, value_normalized, created_at) 
                   VALUES ('m2', 'email', 'a@b.c', 'a@b.c', '2024-01-01')"""
            )
            conn.commit()

            # Invalid type should fail
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """INSERT INTO dim_contact_method 
                       (method_id, type, value_raw, value_normalized, created_at) 
                       VALUES ('m3', 'invalid', 'test', 'test', '2024-01-01')"""
                )
        finally:
            conn.close()


class TestSchemaIndexes:
    """Tests for schema indexes."""

    def test_indexes_exist(self, empty_analysis_db: Path):
        """Required indexes should exist."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';"
            )
            indexes = [row[0] for row in cursor.fetchall()]

            expected_indexes = [
                "idx_contact_method_normalized",
                "idx_contact_method_person",
                "idx_handle_normalized",
                "idx_handle_person",
                "idx_message_date",
                "idx_message_chat",
                "idx_message_handle",
                "idx_message_person",
            ]

            for idx in expected_indexes:
                assert idx in indexes, f"Missing index: {idx}"
        finally:
            conn.close()


class TestSchemaVersion:
    """Tests for schema version tracking."""

    def test_schema_version_stored(self, empty_analysis_db: Path):
        """Schema version should be stored in etl_state."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            cursor = conn.execute("SELECT value FROM etl_state WHERE key = 'schema_version';")
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == SCHEMA_VERSION
        finally:
            conn.close()

    def test_schema_version_constant(self):
        """Schema version should be a valid semver string."""
        assert SCHEMA_VERSION is not None
        parts = SCHEMA_VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()
