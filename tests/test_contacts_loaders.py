"""
Tests for loading contacts data into analysis.db.

Tests loading persons from contacts and contact methods (phones/emails).
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.extractors import (
    Contact,
    ContactPhone,
    ContactEmail,
)
from imessage_analysis.etl.loaders import (
    load_persons_from_contacts,
    load_contact_methods,
    get_loaded_person_count,
    get_loaded_contact_method_count,
    get_contacts_person_count,
)


class TestLoadPersonsFromContacts:
    """Tests for loading persons from contacts."""

    def test_loads_contacts(self, empty_analysis_db: Path):
        """Should load contacts into dim_person."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
                Contact(
                    pk=2, first_name="Jane", last_name="Smith", organization=None, nickname=None
                ),
            ]

            loaded, contact_to_person = load_persons_from_contacts(conn, contacts)

            assert loaded == 2
            assert len(contact_to_person) == 2
            assert get_loaded_person_count(conn) == 2
        finally:
            conn.close()

    def test_generates_unique_person_ids(self, empty_analysis_db: Path):
        """Each contact should get a unique person_id."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
                Contact(
                    pk=2, first_name="Jane", last_name="Smith", organization=None, nickname=None
                ),
            ]

            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            person_ids = list(contact_to_person.values())
            assert len(set(person_ids)) == 2  # All unique
        finally:
            conn.close()

    def test_builds_display_name_from_names(self, empty_analysis_db: Path):
        """Display name should be built from first + last name."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]

            _, contact_to_person = load_persons_from_contacts(conn, contacts)
            person_id = contact_to_person[1]

            cursor = conn.execute(
                "SELECT display_name FROM dim_person WHERE person_id = ?",
                (person_id,),
            )
            display_name = cursor.fetchone()[0]
            assert display_name == "John Doe"
        finally:
            conn.close()

    def test_builds_display_name_from_organization(self, empty_analysis_db: Path):
        """Display name should use organization if no name."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(
                    pk=1, first_name=None, last_name=None, organization="Apple Inc", nickname=None
                ),
            ]

            _, contact_to_person = load_persons_from_contacts(conn, contacts)
            person_id = contact_to_person[1]

            cursor = conn.execute(
                "SELECT display_name FROM dim_person WHERE person_id = ?",
                (person_id,),
            )
            display_name = cursor.fetchone()[0]
            assert display_name == "Apple Inc"
        finally:
            conn.close()

    def test_sets_source_to_contacts(self, empty_analysis_db: Path):
        """Loaded persons should have source='contacts'."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]

            load_persons_from_contacts(conn, contacts)

            cursor = conn.execute("SELECT source FROM dim_person;")
            sources = [row[0] for row in cursor.fetchall()]
            assert all(s == "contacts" for s in sources)
        finally:
            conn.close()

    def test_empty_list(self, empty_analysis_db: Path):
        """Empty list should return 0 and empty mapping."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            loaded, contact_to_person = load_persons_from_contacts(conn, [])

            assert loaded == 0
            assert contact_to_person == {}
        finally:
            conn.close()


class TestLoadContactMethods:
    """Tests for loading contact methods."""

    def test_loads_phones(self, empty_analysis_db: Path):
        """Should load phone numbers into dim_contact_method."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # First create a person
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            # Then load phones
            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            loaded = load_contact_methods(conn, phones, [], contact_to_person)

            assert loaded == 1
            assert get_loaded_contact_method_count(conn) == 1
        finally:
            conn.close()

    def test_loads_emails(self, empty_analysis_db: Path):
        """Should load email addresses into dim_contact_method."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            emails = [
                ContactEmail(pk=1, owner_pk=1, address="john@example.com", label="Home"),
            ]
            loaded = load_contact_methods(conn, [], emails, contact_to_person)

            assert loaded == 1
        finally:
            conn.close()

    def test_normalizes_phone_numbers(self, empty_analysis_db: Path):
        """Phone numbers should be normalized to E.164."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="(415) 555-1234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            cursor = conn.execute("SELECT value_normalized FROM dim_contact_method;")
            normalized = cursor.fetchone()[0]
            assert normalized == "+14155551234"
        finally:
            conn.close()

    def test_normalizes_emails(self, empty_analysis_db: Path):
        """Email addresses should be normalized to lowercase."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            emails = [
                ContactEmail(pk=1, owner_pk=1, address="John.Doe@Example.COM", label="Home"),
            ]
            load_contact_methods(conn, [], emails, contact_to_person)

            cursor = conn.execute("SELECT value_normalized FROM dim_contact_method;")
            normalized = cursor.fetchone()[0]
            assert normalized == "john.doe@example.com"
        finally:
            conn.close()

    def test_skips_orphaned_methods(self, empty_analysis_db: Path):
        """Methods with unknown owner_pk should be skipped."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Create person with pk=1
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            # Try to load phone with owner_pk=999 (doesn't exist)
            phones = [
                ContactPhone(pk=1, owner_pk=999, full_number="+14155551234", label="Mobile"),
            ]
            loaded = load_contact_methods(conn, phones, [], contact_to_person)

            assert loaded == 0
        finally:
            conn.close()

    def test_links_to_correct_person(self, empty_analysis_db: Path):
        """Contact methods should be linked to correct person."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
                Contact(
                    pk=2, first_name="Jane", last_name="Smith", organization=None, nickname=None
                ),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
                ContactPhone(pk=2, owner_pk=2, full_number="+14155555678", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Verify each phone is linked to correct person
            cursor = conn.execute(
                "SELECT person_id, value_raw FROM dim_contact_method ORDER BY value_raw;"
            )
            results = cursor.fetchall()

            assert results[0][0] == contact_to_person[1]  # John's phone
            assert results[1][0] == contact_to_person[2]  # Jane's phone
        finally:
            conn.close()


class TestContactsCounts:
    """Tests for contacts-related count functions."""

    def test_contacts_person_count(self, empty_analysis_db: Path):
        """Should count only contacts-sourced persons."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Load contacts
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            load_persons_from_contacts(conn, contacts)

            # Also insert an inferred person
            conn.execute(
                """INSERT INTO dim_person 
                   (person_id, display_name, source, created_at, updated_at)
                   VALUES ('inferred-1', 'Unknown', 'inferred', '2024-01-01', '2024-01-01')"""
            )
            conn.commit()

            # Should only count contacts
            assert get_contacts_person_count(conn) == 1
            assert get_loaded_person_count(conn) == 2
        finally:
            conn.close()
