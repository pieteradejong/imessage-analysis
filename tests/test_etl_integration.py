"""
End-to-end integration tests for ETL pipeline.

These tests verify the complete ETL flow, including validation.
Tests marked with @pytest.mark.integration may use real data.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.pipeline import run_etl, get_etl_status
from imessage_analysis.etl.validation import validate_etl, ValidationResult
from imessage_analysis.etl.schema import verify_schema


class TestETLIntegration:
    """End-to-end integration tests with sample data."""

    def test_full_pipeline_with_validation(self, sample_chat_db: Path, tmp_path: Path):
        """Full ETL followed by validation should pass."""
        analysis_db = tmp_path / "analysis.db"

        # Run ETL
        etl_result = run_etl(sample_chat_db, analysis_db)
        assert etl_result.success is True

        # Validate
        validation = validate_etl(sample_chat_db, analysis_db)
        assert validation.passed is True

    def test_validation_checks_all_pass(self, sample_chat_db: Path, tmp_path: Path):
        """All validation checks should pass after ETL."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        validation = validate_etl(sample_chat_db, analysis_db)

        # Check individual checks
        for check in validation.checks:
            assert check.passed is True, f"Check failed: {check.name} - {check.message}"

    def test_handle_count_matches(self, sample_chat_db: Path, tmp_path: Path):
        """Handle count in analysis.db should match chat.db."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        # Get source count
        conn = sqlite3.connect(str(sample_chat_db))
        cursor = conn.execute("SELECT COUNT(*) FROM handle")
        source_count = cursor.fetchone()[0]
        conn.close()

        # Get target count
        conn = sqlite3.connect(str(analysis_db))
        cursor = conn.execute("SELECT COUNT(*) FROM dim_handle")
        target_count = cursor.fetchone()[0]
        conn.close()

        assert target_count == source_count

    def test_no_orphan_messages(self, sample_chat_db: Path, tmp_path: Path):
        """All messages should reference valid handles."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        conn = sqlite3.connect(str(analysis_db))
        try:
            cursor = conn.execute(
                """SELECT COUNT(*) FROM fact_message 
                   WHERE handle_id IS NOT NULL 
                   AND handle_id NOT IN (SELECT handle_id FROM dim_handle)"""
            )
            orphan_count = cursor.fetchone()[0]
        finally:
            conn.close()

        assert orphan_count == 0

    def test_all_handles_resolved(self, sample_chat_db: Path, tmp_path: Path):
        """All handles should be resolved to persons."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        conn = sqlite3.connect(str(analysis_db))
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM dim_handle WHERE person_id IS NULL")
            unresolved = cursor.fetchone()[0]
        finally:
            conn.close()

        assert unresolved == 0

    def test_date_format_valid(self, sample_chat_db: Path, tmp_path: Path):
        """All dates should be valid ISO-8601 format."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        conn = sqlite3.connect(str(analysis_db))
        try:
            cursor = conn.execute("SELECT date_utc FROM fact_message")
            dates = [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

        for date in dates:
            assert "T" in date, f"Invalid date format: {date}"
            assert date.endswith("Z"), f"Date not in UTC: {date}"


@pytest.mark.integration
class TestRealDatabaseIntegration:
    """Integration tests with real chat.db.

    These tests are skipped if real chat.db is not available.
    """

    def test_real_etl_completes(self, real_chat_db: Path, real_analysis_db: Path):
        """ETL should complete successfully with real data."""
        result = run_etl(real_chat_db, real_analysis_db)

        assert result.success is True
        assert result.handles_extracted > 0
        assert result.messages_extracted > 0

    def test_real_validation_passes(self, real_chat_db: Path, real_analysis_db: Path):
        """Validation should pass with real data."""
        run_etl(real_chat_db, real_analysis_db)

        validation = validate_etl(real_chat_db, real_analysis_db)

        # Print validation result for debugging
        print(str(validation))

        assert validation.passed is True

    def test_real_incremental_etl(self, real_chat_db: Path, real_analysis_db: Path):
        """Incremental ETL should work with real data."""
        # First run
        first = run_etl(real_chat_db, real_analysis_db)
        assert first.success is True
        assert first.is_incremental is False

        # Second run
        second = run_etl(real_chat_db, real_analysis_db)
        assert second.success is True
        assert second.is_incremental is True

        # Second run should load fewer (ideally zero) new messages
        assert second.messages_loaded <= first.messages_loaded

    def test_real_data_integrity(self, real_chat_db: Path, real_analysis_db: Path):
        """Data integrity checks should pass with real data."""
        run_etl(real_chat_db, real_analysis_db)

        conn = sqlite3.connect(str(real_analysis_db))
        try:
            # No orphan messages
            cursor = conn.execute(
                """SELECT COUNT(*) FROM fact_message 
                   WHERE handle_id IS NOT NULL 
                   AND handle_id NOT IN (SELECT handle_id FROM dim_handle)"""
            )
            assert cursor.fetchone()[0] == 0

            # All handles resolved
            cursor = conn.execute("SELECT COUNT(*) FROM dim_handle WHERE person_id IS NULL")
            assert cursor.fetchone()[0] == 0

            # Schema valid
            assert verify_schema(real_analysis_db) is True
        finally:
            conn.close()


class TestValidationResult:
    """Tests for ValidationResult representation."""

    def test_validation_result_str(self, sample_chat_db: Path, tmp_path: Path):
        """ValidationResult should have readable string representation."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        validation = validate_etl(sample_chat_db, analysis_db)
        result_str = str(validation)

        # Should contain check results
        assert "✓" in result_str or "✗" in result_str
        assert "Handle count" in result_str
        assert "Message count" in result_str

    def test_validation_summary(self, sample_chat_db: Path, tmp_path: Path):
        """Validation should have summary field."""
        analysis_db = tmp_path / "analysis.db"
        run_etl(sample_chat_db, analysis_db)

        validation = validate_etl(sample_chat_db, analysis_db)

        assert validation.summary is not None
        assert "checks passed" in validation.summary
