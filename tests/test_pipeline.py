"""
Tests for ETL pipeline module.

Tests the full ETL pipeline orchestration including incremental updates.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.pipeline import (
    run_etl,
    get_etl_status,
    ETLResult,
)
from imessage_analysis.etl.loaders import get_etl_state


class TestRunETL:
    """Tests for the main ETL pipeline."""

    def test_full_etl_success(self, sample_chat_db: Path, tmp_path: Path):
        """Full ETL should complete successfully."""
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(sample_chat_db, analysis_db)

        assert result.success is True
        assert result.error is None
        assert result.handles_extracted > 0
        assert result.messages_extracted > 0
        assert result.handles_loaded > 0
        assert result.messages_loaded > 0

    def test_etl_creates_analysis_db(self, sample_chat_db: Path, tmp_path: Path):
        """ETL should create analysis.db if it doesn't exist."""
        analysis_db = tmp_path / "analysis.db"
        assert not analysis_db.exists()

        run_etl(sample_chat_db, analysis_db)

        assert analysis_db.exists()

    def test_etl_result_structure(self, sample_chat_db: Path, tmp_path: Path):
        """ETL result should have all expected fields."""
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(sample_chat_db, analysis_db)

        assert isinstance(result, ETLResult)
        assert hasattr(result, "success")
        assert hasattr(result, "handles_extracted")
        assert hasattr(result, "handles_loaded")
        assert hasattr(result, "messages_extracted")
        assert hasattr(result, "messages_loaded")
        assert hasattr(result, "handles_resolved")
        assert hasattr(result, "messages_linked")
        assert hasattr(result, "is_incremental")
        assert hasattr(result, "duration_seconds")

    def test_first_run_is_not_incremental(self, sample_chat_db: Path, tmp_path: Path):
        """First ETL run should not be incremental."""
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(sample_chat_db, analysis_db)

        assert result.is_incremental is False

    def test_second_run_is_incremental(self, sample_chat_db: Path, tmp_path: Path):
        """Second ETL run should be incremental."""
        analysis_db = tmp_path / "analysis.db"

        # First run
        run_etl(sample_chat_db, analysis_db)

        # Second run
        result = run_etl(sample_chat_db, analysis_db)

        assert result.is_incremental is True

    def test_incremental_loads_zero_duplicates(self, sample_chat_db: Path, tmp_path: Path):
        """Incremental run should not re-load existing messages."""
        analysis_db = tmp_path / "analysis.db"

        # First run
        first = run_etl(sample_chat_db, analysis_db)

        # Second run (incremental)
        second = run_etl(sample_chat_db, analysis_db)

        # Second run should load 0 new messages (all already exist)
        assert second.messages_loaded == 0
        # But should still extract handles (for upsert)
        assert second.handles_extracted == first.handles_extracted

    def test_force_full_ignores_state(self, sample_chat_db: Path, tmp_path: Path):
        """force_full=True should ignore incremental state."""
        analysis_db = tmp_path / "analysis.db"

        # First run
        run_etl(sample_chat_db, analysis_db)

        # Second run with force_full
        result = run_etl(sample_chat_db, analysis_db, force_full=True)

        assert result.is_incremental is False

    def test_updates_etl_state(self, sample_chat_db: Path, tmp_path: Path):
        """ETL should update etl_state table."""
        analysis_db = tmp_path / "analysis.db"

        run_etl(sample_chat_db, analysis_db)

        conn = sqlite3.connect(str(analysis_db))
        try:
            last_sync = get_etl_state(conn, "last_sync")
            last_message = get_etl_state(conn, "last_message_date")

            assert last_sync is not None
            assert "T" in last_sync  # ISO-8601 format
        finally:
            conn.close()

    def test_empty_chat_db(self, empty_chat_db: Path, tmp_path: Path):
        """ETL with empty chat.db should complete with zero counts."""
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(empty_chat_db, analysis_db)

        assert result.success is True
        assert result.handles_extracted == 0
        assert result.messages_extracted == 0

    def test_invalid_chat_db_path(self, tmp_path: Path):
        """ETL with non-existent chat.db should fail gracefully."""
        chat_db = tmp_path / "nonexistent.db"
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(chat_db, analysis_db)

        assert result.success is False
        assert result.error is not None

    def test_result_str_representation(self, sample_chat_db: Path, tmp_path: Path):
        """ETL result should have readable string representation."""
        analysis_db = tmp_path / "analysis.db"

        result = run_etl(sample_chat_db, analysis_db)
        result_str = str(result)

        assert "SUCCESS" in result_str or "FAILED" in result_str
        assert "Handles" in result_str
        assert "Messages" in result_str


class TestGetETLStatus:
    """Tests for ETL status function."""

    def test_nonexistent_database(self, tmp_path: Path):
        """Non-existent database should return exists=False."""
        analysis_db = tmp_path / "nonexistent.db"

        status = get_etl_status(analysis_db)

        assert status["exists"] is False

    def test_after_etl(self, sample_chat_db: Path, tmp_path: Path):
        """Status after ETL should show counts and timestamps."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        status = get_etl_status(analysis_db)

        assert status["exists"] is True
        assert status["schema_valid"] is True
        assert status["handle_count"] > 0
        assert status["message_count"] > 0
        assert status["last_sync"] is not None
        assert status["schema_version"] is not None


class TestETLIdempotency:
    """Tests for ETL idempotency."""

    def test_multiple_runs_same_result(self, sample_chat_db: Path, tmp_path: Path):
        """Multiple ETL runs should produce same data counts."""
        analysis_db = tmp_path / "analysis.db"

        # Run ETL three times
        run_etl(sample_chat_db, analysis_db)
        run_etl(sample_chat_db, analysis_db)
        run_etl(sample_chat_db, analysis_db)

        status = get_etl_status(analysis_db)

        # Counts should match source
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM handle")
            source_handles = cursor.fetchone()[0]
            cursor = conn.execute("SELECT COUNT(*) FROM message")
            source_messages = cursor.fetchone()[0]
        finally:
            conn.close()

        assert status["handle_count"] == source_handles
        # Message count may be less due to filtering, but should not exceed source
        assert status["message_count"] <= source_messages
