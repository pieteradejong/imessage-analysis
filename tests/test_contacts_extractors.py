"""
Tests for contacts extraction from AddressBook database.

Tests the extraction of contacts, phone numbers, and email addresses
from the Core Data schema used by Apple's Contacts app.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.extractors import (
    extract_contacts,
    extract_contact_phones,
    extract_contact_emails,
    get_contact_count,
    Contact,
    ContactPhone,
    ContactEmail,
)


class TestExtractContacts:
    """Tests for contact extraction."""

    def test_extracts_all_contacts(self, sample_contacts_db: Path):
        """Should extract all contacts from AddressBook."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            contacts = extract_contacts(conn)
            assert len(contacts) == 4  # We inserted 4 contacts
        finally:
            conn.close()

    def test_contact_structure(self, sample_contacts_db: Path):
        """Extracted contacts should have correct structure."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            contacts = extract_contacts(conn)

            for contact in contacts:
                assert isinstance(contact, Contact)
                assert contact.pk > 0
        finally:
            conn.close()

    def test_contact_with_full_name(self, sample_contacts_db: Path):
        """Contact with first and last name should be extracted."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            contacts = extract_contacts(conn)

            john = next((c for c in contacts if c.first_name == "John"), None)
            assert john is not None
            assert john.last_name == "Doe"
        finally:
            conn.close()

    def test_contact_with_organization_only(self, sample_contacts_db: Path):
        """Contact with only organization should be extracted."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            contacts = extract_contacts(conn)

            apple = next((c for c in contacts if c.organization == "Apple Inc"), None)
            assert apple is not None
            assert apple.first_name is None
            assert apple.last_name is None
        finally:
            conn.close()

    def test_empty_database(self, empty_contacts_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_contacts_db))
        try:
            contacts = extract_contacts(conn)
            assert contacts == []
        finally:
            conn.close()


class TestExtractContactPhones:
    """Tests for phone number extraction."""

    def test_extracts_all_phones(self, sample_contacts_db: Path):
        """Should extract all phone numbers."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            phones = extract_contact_phones(conn)
            assert len(phones) == 4  # We inserted 4 phone numbers
        finally:
            conn.close()

    def test_phone_structure(self, sample_contacts_db: Path):
        """Extracted phones should have correct structure."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            phones = extract_contact_phones(conn)

            for phone in phones:
                assert isinstance(phone, ContactPhone)
                assert phone.pk > 0
                assert phone.owner_pk > 0
                assert phone.full_number is not None
        finally:
            conn.close()

    def test_phone_linked_to_contact(self, sample_contacts_db: Path):
        """Phone should have valid owner_pk linking to contact."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            phones = extract_contact_phones(conn)
            contacts = extract_contacts(conn)

            contact_pks = {c.pk for c in contacts}

            for phone in phones:
                assert phone.owner_pk in contact_pks
        finally:
            conn.close()

    def test_phone_with_label(self, sample_contacts_db: Path):
        """Phone should have label (mobile, home, work, etc.)."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            phones = extract_contact_phones(conn)

            # At least some phones should have labels
            phones_with_labels = [p for p in phones if p.label]
            assert len(phones_with_labels) > 0
        finally:
            conn.close()

    def test_empty_database(self, empty_contacts_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_contacts_db))
        try:
            phones = extract_contact_phones(conn)
            assert phones == []
        finally:
            conn.close()


class TestExtractContactEmails:
    """Tests for email address extraction."""

    def test_extracts_all_emails(self, sample_contacts_db: Path):
        """Should extract all email addresses."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            emails = extract_contact_emails(conn)
            assert len(emails) == 3  # We inserted 3 email addresses
        finally:
            conn.close()

    def test_email_structure(self, sample_contacts_db: Path):
        """Extracted emails should have correct structure."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            emails = extract_contact_emails(conn)

            for email in emails:
                assert isinstance(email, ContactEmail)
                assert email.pk > 0
                assert email.owner_pk > 0
                assert email.address is not None
                assert "@" in email.address
        finally:
            conn.close()

    def test_email_linked_to_contact(self, sample_contacts_db: Path):
        """Email should have valid owner_pk linking to contact."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            emails = extract_contact_emails(conn)
            contacts = extract_contacts(conn)

            contact_pks = {c.pk for c in contacts}

            for email in emails:
                assert email.owner_pk in contact_pks
        finally:
            conn.close()

    def test_empty_database(self, empty_contacts_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_contacts_db))
        try:
            emails = extract_contact_emails(conn)
            assert emails == []
        finally:
            conn.close()


class TestGetContactCount:
    """Tests for contact count function."""

    def test_count_with_data(self, sample_contacts_db: Path):
        """Should return correct contact count."""
        conn = sqlite3.connect(str(sample_contacts_db))
        try:
            count = get_contact_count(conn)
            assert count == 4
        finally:
            conn.close()

    def test_count_empty_database(self, empty_contacts_db: Path):
        """Empty database should return zero."""
        conn = sqlite3.connect(str(empty_contacts_db))
        try:
            count = get_contact_count(conn)
            assert count == 0
        finally:
            conn.close()


@pytest.mark.integration
class TestRealContactsExtraction:
    """Integration tests with real Contacts database."""

    def test_extract_real_contacts(self, real_contacts_db: Path):
        """Should extract contacts from real AddressBook."""
        conn = sqlite3.connect(f"file:{real_contacts_db}?mode=ro", uri=True)
        try:
            contacts = extract_contacts(conn)

            # Real database should have at least some contacts
            assert len(contacts) > 0

            # Verify structure
            for contact in contacts[:10]:  # Check first 10
                assert isinstance(contact, Contact)
                assert contact.pk > 0
        finally:
            conn.close()

    def test_extract_real_phones(self, real_contacts_db: Path):
        """Should extract phones from real AddressBook."""
        conn = sqlite3.connect(f"file:{real_contacts_db}?mode=ro", uri=True)
        try:
            phones = extract_contact_phones(conn)

            # Should have at least some phone numbers
            assert len(phones) >= 0  # May be empty if no phone numbers

            for phone in phones[:10]:
                assert isinstance(phone, ContactPhone)
        finally:
            conn.close()

    def test_extract_real_emails(self, real_contacts_db: Path):
        """Should extract emails from real AddressBook."""
        conn = sqlite3.connect(f"file:{real_contacts_db}?mode=ro", uri=True)
        try:
            emails = extract_contact_emails(conn)

            # Should have at least some email addresses
            assert len(emails) >= 0  # May be empty if no emails

            for email in emails[:10]:
                assert isinstance(email, ContactEmail)
                assert "@" in email.address
        finally:
            conn.close()
