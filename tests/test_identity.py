"""
Tests for ETL identity resolution module.

Tests identity resolution, person creation, and handle-to-person linking.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.identity import (
    resolve_handle_to_person,
    create_unknown_person,
    link_handle_to_person,
    resolve_all_handles,
    get_unresolved_handle_count,
    get_inferred_person_count,
)


class TestResolveHandleToPerson:
    """Tests for handle-to-person resolution."""

    def test_no_match_returns_none(self, empty_analysis_db: Path):
        """Unmatched handle should return None."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            result = resolve_handle_to_person(conn, "+14155551234")
            assert result is None
        finally:
            conn.close()

    def test_match_via_contact_method(self, empty_analysis_db: Path):
        """Should find person via dim_contact_method match."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert a person and contact method
            conn.execute(
                """INSERT INTO dim_person 
                   (person_id, display_name, source, created_at, updated_at)
                   VALUES ('person-123', 'John Doe', 'contacts', '2024-01-01', '2024-01-01')"""
            )
            conn.execute(
                """INSERT INTO dim_contact_method
                   (method_id, person_id, type, value_raw, value_normalized, created_at)
                   VALUES ('m1', 'person-123', 'phone', '+1 (415) 555-1234', '+14155551234', '2024-01-01')"""
            )
            conn.commit()

            # Resolve the handle
            result = resolve_handle_to_person(conn, "+14155551234")
            assert result == "person-123"
        finally:
            conn.close()


class TestCreateUnknownPerson:
    """Tests for creating placeholder persons."""

    def test_creates_person(self, empty_analysis_db: Path):
        """Should create a new person record."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            person_id = create_unknown_person(conn, "+14155551234", "phone")

            assert person_id is not None
            assert len(person_id) > 0

            # Verify person exists
            cursor = conn.execute(
                "SELECT display_name, source FROM dim_person WHERE person_id = ?",
                (person_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert "Unknown" in row[0]
            assert row[1] == "inferred"
        finally:
            conn.close()

    def test_phone_display_name(self, empty_analysis_db: Path):
        """Phone handle should show number in display name."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            person_id = create_unknown_person(conn, "+14155551234", "phone")

            cursor = conn.execute(
                "SELECT display_name FROM dim_person WHERE person_id = ?",
                (person_id,),
            )
            display_name = cursor.fetchone()[0]
            assert "+14155551234" in display_name
        finally:
            conn.close()

    def test_email_display_name(self, empty_analysis_db: Path):
        """Email handle should show local part in display name."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            person_id = create_unknown_person(conn, "john.doe@example.com", "email")

            cursor = conn.execute(
                "SELECT display_name FROM dim_person WHERE person_id = ?",
                (person_id,),
            )
            display_name = cursor.fetchone()[0]
            assert "john.doe" in display_name
        finally:
            conn.close()

    def test_unique_person_ids(self, empty_analysis_db: Path):
        """Each call should create a unique person ID."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            id1 = create_unknown_person(conn, "+1111", "phone")
            id2 = create_unknown_person(conn, "+2222", "phone")
            id3 = create_unknown_person(conn, "+3333", "phone")

            assert id1 != id2
            assert id2 != id3
            assert id1 != id3
        finally:
            conn.close()


class TestLinkHandleToPerson:
    """Tests for linking handles to persons."""

    def test_links_handle(self, empty_analysis_db: Path):
        """Should update handle with person_id."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert a handle without person_id
            conn.execute(
                """INSERT INTO dim_handle
                   (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at)
                   VALUES (1, '+14155551234', '+14155551234', 'phone', '2024-01-01', '2024-01-01')"""
            )
            conn.commit()

            # Link to a person
            link_handle_to_person(conn, 1, "person-abc")

            # Verify
            cursor = conn.execute("SELECT person_id FROM dim_handle WHERE handle_id = 1")
            assert cursor.fetchone()[0] == "person-abc"
        finally:
            conn.close()


class TestResolveAllHandles:
    """Tests for bulk handle resolution."""

    def test_resolves_all_unlinked_handles(self, empty_analysis_db: Path):
        """Should resolve all handles without person_id."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert handles without person_id
            for i in range(1, 4):
                conn.execute(
                    """INSERT INTO dim_handle
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at)
                       VALUES (?, ?, ?, 'phone', '2024-01-01', '2024-01-01')""",
                    (i, f"+1{i}", f"+1{i}"),
                )
            conn.commit()

            # Resolve all
            resolved = resolve_all_handles(conn)

            assert resolved == 3
            assert get_unresolved_handle_count(conn) == 0
        finally:
            conn.close()

    def test_creates_inferred_persons(self, empty_analysis_db: Path):
        """Should create inferred persons for unmatched handles."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert handles
            for i in range(1, 4):
                conn.execute(
                    """INSERT INTO dim_handle
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at)
                       VALUES (?, ?, ?, 'phone', '2024-01-01', '2024-01-01')""",
                    (i, f"+1{i}", f"+1{i}"),
                )
            conn.commit()

            # Resolve all
            resolve_all_handles(conn)

            # Check persons were created
            assert get_inferred_person_count(conn) == 3
        finally:
            conn.close()

    def test_skips_already_linked_handles(self, empty_analysis_db: Path):
        """Should not re-resolve already linked handles."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert a person
            conn.execute(
                """INSERT INTO dim_person
                   (person_id, display_name, source, created_at, updated_at)
                   VALUES ('existing-person', 'John', 'contacts', '2024-01-01', '2024-01-01')"""
            )

            # Insert a handle already linked
            conn.execute(
                """INSERT INTO dim_handle
                   (handle_id, value_raw, value_normalized, handle_type, person_id, created_at, updated_at)
                   VALUES (1, '+1234', '+1234', 'phone', 'existing-person', '2024-01-01', '2024-01-01')"""
            )

            # Insert an unlinked handle
            conn.execute(
                """INSERT INTO dim_handle
                   (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at)
                   VALUES (2, '+5678', '+5678', 'phone', '2024-01-01', '2024-01-01')"""
            )
            conn.commit()

            # Resolve
            resolved = resolve_all_handles(conn)

            # Should only resolve the unlinked one
            assert resolved == 1
        finally:
            conn.close()

    def test_no_unresolved_handles(self, empty_analysis_db: Path):
        """No unresolved handles should return 0."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            resolved = resolve_all_handles(conn)
            assert resolved == 0
        finally:
            conn.close()


class TestGetCounts:
    """Tests for count functions."""

    def test_unresolved_count(self, empty_analysis_db: Path):
        """Should count handles without person_id."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Insert unresolved handles
            for i in range(1, 4):
                conn.execute(
                    """INSERT INTO dim_handle
                       (handle_id, value_raw, value_normalized, handle_type, created_at, updated_at)
                       VALUES (?, ?, ?, 'phone', '2024-01-01', '2024-01-01')""",
                    (i, f"+1{i}", f"+1{i}"),
                )
            conn.commit()

            assert get_unresolved_handle_count(conn) == 3
        finally:
            conn.close()

    def test_inferred_person_count(self, empty_analysis_db: Path):
        """Should count persons with source='inferred'."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Create some inferred persons
            for i in range(1, 4):
                create_unknown_person(conn, f"+1{i}", "phone")

            assert get_inferred_person_count(conn) == 3
        finally:
            conn.close()

    def test_empty_database(self, empty_analysis_db: Path):
        """Empty database should return zero counts."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            assert get_unresolved_handle_count(conn) == 0
            assert get_inferred_person_count(conn) == 0
        finally:
            conn.close()
