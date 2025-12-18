"""
End-to-end integration tests for contacts integration.

Tests the full pipeline with contacts database support.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.pipeline import run_etl, get_etl_status
from imessage_analysis.etl.validation import validate_etl
from imessage_analysis.etl.loaders import (
    get_loaded_person_count,
    get_loaded_contact_method_count,
    get_contacts_person_count,
)


class TestContactsIntegration:
    """Integration tests with sample contacts database."""

    def test_pipeline_with_contacts(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Pipeline should successfully sync contacts."""
        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        assert result.success
        assert result.contacts_synced
        assert result.contacts_extracted == 4  # 4 contacts in sample
        assert result.contact_methods_loaded > 0

    def test_pipeline_without_contacts(self, sample_chat_db: Path, empty_analysis_db: Path):
        """Pipeline should work without contacts."""
        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=None,
        )

        assert result.success
        assert not result.contacts_synced
        assert result.contacts_extracted == 0

    def test_contacts_loaded_into_dim_person(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Contacts should be loaded into dim_person."""
        run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Should have contacts-sourced persons
            contacts_count = get_contacts_person_count(conn)
            assert contacts_count == 4
        finally:
            conn.close()

    def test_contact_methods_loaded(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Contact methods should be loaded into dim_contact_method."""
        run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            count = get_loaded_contact_method_count(conn)
            # 4 phones + 3 emails in sample
            assert count == 7
        finally:
            conn.close()

    def test_handle_resolved_to_contact(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Handles matching contacts should be linked to contact persons."""
        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        # Some handles should have been resolved
        assert result.handles_resolved > 0

    def test_etl_status_includes_contacts(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """ETL status should include contacts information."""
        run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        status = get_etl_status(empty_analysis_db)

        assert "person_count" in status
        assert "contact_method_count" in status
        assert "last_contacts_sync" in status
        assert status["person_count"] > 0

    def test_validation_with_contacts(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Validation should pass with contacts data."""
        run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )

        result = validate_etl(sample_chat_db, empty_analysis_db)

        assert result.passed

        # Check contacts-specific validations
        contacts_check = next((c for c in result.checks if "Contacts" in c.name), None)
        assert contacts_check is not None


class TestContactsGracefulHandling:
    """Tests for graceful handling of contacts issues."""

    def test_invalid_contacts_path(
        self, sample_chat_db: Path, empty_analysis_db: Path, tmp_path: Path
    ):
        """Invalid contacts path should not fail the pipeline."""
        fake_path = tmp_path / "nonexistent.abcddb"

        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=fake_path,
        )

        # Pipeline should succeed, just without contacts
        assert result.success
        assert not result.contacts_synced

    def test_empty_contacts_db(
        self, sample_chat_db: Path, empty_analysis_db: Path, empty_contacts_db: Path
    ):
        """Empty contacts database should work fine."""
        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=empty_contacts_db,
        )

        assert result.success
        assert result.contacts_synced
        assert result.contacts_extracted == 0


class TestIncrementalWithContacts:
    """Tests for incremental ETL with contacts."""

    def test_incremental_preserves_contacts(
        self, sample_chat_db: Path, empty_analysis_db: Path, sample_contacts_db: Path
    ):
        """Incremental runs should preserve contacts data."""
        # First run
        result1 = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=sample_contacts_db,
        )
        assert result1.success

        conn = sqlite3.connect(str(empty_analysis_db))
        persons_after_first = get_loaded_person_count(conn)
        conn.close()

        # Second run (incremental, no contacts this time)
        result2 = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=None,  # No contacts
        )
        assert result2.success

        conn = sqlite3.connect(str(empty_analysis_db))
        persons_after_second = get_loaded_person_count(conn)
        conn.close()

        # Persons should be preserved
        assert persons_after_second >= persons_after_first


@pytest.mark.integration
class TestRealContactsIntegration:
    """Integration tests with real contacts database."""

    def test_real_contacts_extraction(
        self, sample_chat_db: Path, empty_analysis_db: Path, real_contacts_db: Path
    ):
        """Should work with real contacts database."""
        result = run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=real_contacts_db,
        )

        assert result.success
        assert result.contacts_synced
        # Real contacts should have at least some contacts
        assert result.contacts_extracted > 0

    def test_real_contacts_validation(
        self, sample_chat_db: Path, empty_analysis_db: Path, real_contacts_db: Path
    ):
        """Validation should pass with real contacts."""
        run_etl(
            chat_db_path=sample_chat_db,
            analysis_db_path=empty_analysis_db,
            contacts_db_path=real_contacts_db,
        )

        result = validate_etl(sample_chat_db, empty_analysis_db)

        assert result.passed
