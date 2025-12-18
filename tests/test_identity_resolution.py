"""
Tests for enhanced identity resolution with contacts matching.

Tests the resolution of handles to persons using both exact and fuzzy matching.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.extractors import Contact, ContactPhone, ContactEmail
from imessage_analysis.etl.loaders import (
    load_handles,
    load_persons_from_contacts,
    load_contact_methods,
)
from imessage_analysis.etl.extractors import Handle
from imessage_analysis.etl.identity import (
    resolve_handle_to_person,
    resolve_all_handles,
    create_unknown_person,
    get_handles_linked_to_contacts_count,
    get_inferred_person_count,
    get_contacts_person_count,
)


class TestResolveHandleToPerson:
    """Tests for resolve_handle_to_person function."""

    def test_exact_match_phone(self, empty_analysis_db: Path):
        """Should match handle to contact by exact phone match."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Set up contact with phone
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Resolve handle with same normalized phone
            person_id = resolve_handle_to_person(conn, "+14155551234", "phone")

            assert person_id == contact_to_person[1]
        finally:
            conn.close()

    def test_exact_match_email(self, empty_analysis_db: Path):
        """Should match handle to contact by exact email match."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            emails = [
                ContactEmail(pk=1, owner_pk=1, address="john@example.com", label="Home"),
            ]
            load_contact_methods(conn, [], emails, contact_to_person)

            # Resolve handle with same email
            person_id = resolve_handle_to_person(conn, "john@example.com", "email")

            assert person_id == contact_to_person[1]
        finally:
            conn.close()

    def test_fuzzy_phone_match_last_10_digits(self, empty_analysis_db: Path):
        """Should match phone by last 10 digits for fuzzy matching."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            # Contact has US format
            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Handle has same number with different format/country code
            # Last 10 digits are 4155551234
            person_id = resolve_handle_to_person(conn, "+14155551234", "phone")
            assert person_id == contact_to_person[1]

        finally:
            conn.close()

    def test_no_match_returns_none(self, empty_analysis_db: Path):
        """Should return None if no matching contact method."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Try to resolve a different phone
            person_id = resolve_handle_to_person(conn, "+19875551234", "phone")

            assert person_id is None
        finally:
            conn.close()

    def test_email_no_fuzzy_match(self, empty_analysis_db: Path):
        """Emails should only match exactly, no fuzzy matching."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            emails = [
                ContactEmail(pk=1, owner_pk=1, address="john@example.com", label="Home"),
            ]
            load_contact_methods(conn, [], emails, contact_to_person)

            # Similar but different email should not match
            person_id = resolve_handle_to_person(conn, "john@different.com", "email")

            assert person_id is None
        finally:
            conn.close()


class TestResolveAllHandles:
    """Tests for resolve_all_handles with contacts."""

    def test_links_handles_to_contacts(self, empty_analysis_db: Path):
        """Handles should be linked to contact persons when matching."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Set up contacts
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Load handle with matching phone
            handles = [
                Handle(
                    rowid=1,
                    value_raw="+1 (415) 555-1234",
                    value_normalized="+14155551234",
                    handle_type="phone",
                    service="iMessage",
                    country="us",
                ),
            ]
            load_handles(conn, handles)

            # Resolve handles
            resolved = resolve_all_handles(conn)

            assert resolved == 1
            assert get_handles_linked_to_contacts_count(conn) == 1
            assert get_inferred_person_count(conn) == 0
        finally:
            conn.close()

    def test_creates_inferred_for_unmatched(self, empty_analysis_db: Path):
        """Handles without matching contacts should get inferred persons."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Set up contacts (but with different phone)
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            # Load handle with different phone
            handles = [
                Handle(
                    rowid=1,
                    value_raw="+1 (510) 555-9999",
                    value_normalized="+15105559999",
                    handle_type="phone",
                    service="iMessage",
                    country="us",
                ),
            ]
            load_handles(conn, handles)

            # Resolve handles
            resolve_all_handles(conn)

            assert get_handles_linked_to_contacts_count(conn) == 0
            assert get_inferred_person_count(conn) == 1
        finally:
            conn.close()

    def test_mixed_matched_and_unmatched(self, empty_analysis_db: Path):
        """Should handle mix of matched and unmatched handles."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            emails = [
                ContactEmail(pk=1, owner_pk=1, address="john@example.com", label="Home"),
            ]
            load_contact_methods(conn, phones, emails, contact_to_person)

            # Load handles - one matches, one doesn't
            handles = [
                Handle(
                    rowid=1,
                    value_raw="+14155551234",
                    value_normalized="+14155551234",
                    handle_type="phone",
                    service="iMessage",
                    country="us",
                ),
                Handle(
                    rowid=2,
                    value_raw="unknown@other.com",
                    value_normalized="unknown@other.com",
                    handle_type="email",
                    service="iMessage",
                    country=None,
                ),
            ]
            load_handles(conn, handles)

            # Resolve handles
            resolved = resolve_all_handles(conn)

            assert resolved == 2
            assert get_handles_linked_to_contacts_count(conn) == 1
            assert get_inferred_person_count(conn) == 1
        finally:
            conn.close()


class TestIdentityResolutionCounts:
    """Tests for identity resolution count functions."""

    def test_contacts_person_count(self, empty_analysis_db: Path):
        """Should count persons from contacts."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
                Contact(
                    pk=2, first_name="Jane", last_name="Smith", organization=None, nickname=None
                ),
            ]
            load_persons_from_contacts(conn, contacts)

            assert get_contacts_person_count(conn) == 2
        finally:
            conn.close()

    def test_handles_linked_to_contacts(self, empty_analysis_db: Path):
        """Should count handles linked to contacts-sourced persons."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            contacts = [
                Contact(pk=1, first_name="John", last_name="Doe", organization=None, nickname=None),
            ]
            _, contact_to_person = load_persons_from_contacts(conn, contacts)

            phones = [
                ContactPhone(pk=1, owner_pk=1, full_number="+14155551234", label="Mobile"),
            ]
            load_contact_methods(conn, phones, [], contact_to_person)

            handles = [
                Handle(
                    rowid=1,
                    value_raw="+14155551234",
                    value_normalized="+14155551234",
                    handle_type="phone",
                    service="iMessage",
                    country="us",
                ),
            ]
            load_handles(conn, handles)
            resolve_all_handles(conn)

            assert get_handles_linked_to_contacts_count(conn) == 1
        finally:
            conn.close()
