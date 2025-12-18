"""
Tests for ETL extractors module.

Tests data extraction from chat.db including handles, messages, and chats.
"""

import sqlite3
from pathlib import Path

import pytest

from imessage_analysis.etl.extractors import (
    extract_handles,
    extract_messages,
    extract_chats,
    get_handle_count,
    get_message_count,
    get_latest_message_date,
    Handle,
    Message,
    Chat,
)


class TestExtractHandles:
    """Tests for handle extraction."""

    def test_extracts_all_handles(self, sample_chat_db: Path):
        """Should extract all handles from chat.db."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            handles = extract_handles(conn)

            assert len(handles) == 5  # We inserted 5 handles in fixture
        finally:
            conn.close()

    def test_handle_structure(self, sample_chat_db: Path):
        """Extracted handles should have correct structure."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            handles = extract_handles(conn)

            for handle in handles:
                assert isinstance(handle, Handle)
                assert handle.rowid > 0
                assert handle.value_raw is not None
                assert handle.value_normalized is not None
                assert handle.handle_type in ("phone", "email", "unknown")
        finally:
            conn.close()

    def test_phone_normalization(self, sample_chat_db: Path):
        """Phone handles should be normalized."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            handles = extract_handles(conn)

            # Find the phone handle
            phone_handles = [h for h in handles if h.handle_type == "phone"]
            assert len(phone_handles) >= 1

            for h in phone_handles:
                # Normalized phone should start with +
                assert h.value_normalized.startswith("+")
        finally:
            conn.close()

    def test_email_normalization(self, sample_chat_db: Path):
        """Email handles should be normalized."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            handles = extract_handles(conn)

            # Find the email handle
            email_handles = [h for h in handles if h.handle_type == "email"]
            assert len(email_handles) >= 1

            for h in email_handles:
                # Normalized email should be lowercase
                assert h.value_normalized == h.value_normalized.lower()
        finally:
            conn.close()

    def test_empty_database(self, empty_chat_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_chat_db))
        try:
            handles = extract_handles(conn)
            assert handles == []
        finally:
            conn.close()


class TestExtractMessages:
    """Tests for message extraction."""

    def test_extracts_all_messages(self, sample_chat_db: Path):
        """Should extract all messages from chat.db."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            messages = extract_messages(conn)

            assert len(messages) == 7  # We inserted 7 messages in fixture
        finally:
            conn.close()

    def test_message_structure(self, sample_chat_db: Path):
        """Extracted messages should have correct structure."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            messages = extract_messages(conn)

            for msg in messages:
                assert isinstance(msg, Message)
                assert msg.rowid > 0
                assert msg.date_utc is not None
                assert isinstance(msg.is_from_me, bool)
        finally:
            conn.close()

    def test_message_date_format(self, sample_chat_db: Path):
        """Message dates should be ISO-8601 format."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            messages = extract_messages(conn)

            for msg in messages:
                # Should be ISO-8601 format: YYYY-MM-DDTHH:MM:SSZ
                assert "T" in msg.date_utc
                assert msg.date_utc.endswith("Z")
        finally:
            conn.close()

    def test_message_chat_id(self, sample_chat_db: Path):
        """Messages should have chat_id from join table."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            messages = extract_messages(conn)

            # Most messages should have chat_id
            messages_with_chat = [m for m in messages if m.chat_id is not None]
            assert len(messages_with_chat) >= 1
        finally:
            conn.close()

    def test_incremental_extraction(self, sample_chat_db: Path):
        """Incremental extraction should filter by date."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            # First, get all messages
            all_messages = extract_messages(conn)

            # Then extract with a future date (should get none)
            future_messages = extract_messages(conn, since_date="2030-01-01T00:00:00Z")
            assert len(future_messages) == 0

            # Extract with a past date (should get all)
            past_messages = extract_messages(conn, since_date="2020-01-01T00:00:00Z")
            assert len(past_messages) == len(all_messages)
        finally:
            conn.close()

    def test_empty_database(self, empty_chat_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_chat_db))
        try:
            messages = extract_messages(conn)
            assert messages == []
        finally:
            conn.close()


class TestExtractChats:
    """Tests for chat extraction."""

    def test_extracts_all_chats(self, sample_chat_db: Path):
        """Should extract all chats from chat.db."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            chats = extract_chats(conn)

            assert len(chats) == 3  # We inserted 3 chats in fixture
        finally:
            conn.close()

    def test_chat_structure(self, sample_chat_db: Path):
        """Extracted chats should have correct structure."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            chats = extract_chats(conn)

            for chat in chats:
                assert isinstance(chat, Chat)
                assert chat.rowid > 0
                assert chat.chat_identifier is not None
        finally:
            conn.close()

    def test_empty_database(self, empty_chat_db: Path):
        """Empty database should return empty list."""
        conn = sqlite3.connect(str(empty_chat_db))
        try:
            chats = extract_chats(conn)
            assert chats == []
        finally:
            conn.close()


class TestGetCounts:
    """Tests for count functions."""

    def test_get_handle_count(self, sample_chat_db: Path):
        """Should return correct handle count."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            count = get_handle_count(conn)
            assert count == 5
        finally:
            conn.close()

    def test_get_message_count(self, sample_chat_db: Path):
        """Should return correct message count."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            count = get_message_count(conn)
            assert count == 7
        finally:
            conn.close()

    def test_empty_database_counts(self, empty_chat_db: Path):
        """Empty database should return zero counts."""
        conn = sqlite3.connect(str(empty_chat_db))
        try:
            assert get_handle_count(conn) == 0
            assert get_message_count(conn) == 0
        finally:
            conn.close()


class TestGetLatestMessageDate:
    """Tests for latest message date function."""

    def test_returns_date(self, sample_chat_db: Path):
        """Should return the latest message date."""
        conn = sqlite3.connect(str(sample_chat_db))
        try:
            date = get_latest_message_date(conn)

            assert date is not None
            assert "T" in date
            assert date.endswith("Z")
        finally:
            conn.close()

    def test_empty_database_returns_none(self, empty_chat_db: Path):
        """Empty database should return None."""
        conn = sqlite3.connect(str(empty_chat_db))
        try:
            date = get_latest_message_date(conn)
            assert date is None
        finally:
            conn.close()
