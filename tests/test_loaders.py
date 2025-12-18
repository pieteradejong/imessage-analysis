"""
Tests for ETL loaders module.

Tests data loading into analysis.db including handles, messages, and ETL state.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from imessage_analysis.etl.extractors import Handle, Message
from imessage_analysis.etl.loaders import (
    load_handles,
    load_messages,
    update_etl_state,
    get_etl_state,
    get_loaded_handle_count,
    get_loaded_message_count,
    link_messages_to_persons,
)


class TestLoadHandles:
    """Tests for handle loading."""

    def test_loads_handles(self, empty_analysis_db: Path):
        """Should load handles into dim_handle."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            handles = [
                Handle(
                    rowid=1,
                    value_raw="+14155551234",
                    value_normalized="+14155551234",
                    handle_type="phone",
                ),
                Handle(
                    rowid=2,
                    value_raw="user@example.com",
                    value_normalized="user@example.com",
                    handle_type="email",
                ),
            ]

            loaded = load_handles(conn, handles)

            assert loaded == 2
            assert get_loaded_handle_count(conn) == 2
        finally:
            conn.close()

    def test_upsert_behavior(self, empty_analysis_db: Path):
        """Loading same handle twice should update, not duplicate."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            handle = Handle(
                rowid=1,
                value_raw="+14155551234",
                value_normalized="+14155551234",
                handle_type="phone",
            )

            # Load twice
            load_handles(conn, [handle])
            load_handles(conn, [handle])

            # Should still be 1 handle
            assert get_loaded_handle_count(conn) == 1
        finally:
            conn.close()

    def test_empty_list(self, empty_analysis_db: Path):
        """Empty list should return 0."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            loaded = load_handles(conn, [])
            assert loaded == 0
        finally:
            conn.close()


class TestLoadMessages:
    """Tests for message loading."""

    def test_loads_messages(self, empty_analysis_db: Path):
        """Should load messages into fact_message."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            messages = [
                Message(
                    rowid=1,
                    chat_id=1,
                    handle_id=1,
                    text="Hello!",
                    date_utc="2024-01-15T10:00:00Z",
                    date_local=None,
                    is_from_me=False,
                ),
                Message(
                    rowid=2,
                    chat_id=1,
                    handle_id=None,
                    text="Hi there!",
                    date_utc="2024-01-15T10:01:00Z",
                    date_local=None,
                    is_from_me=True,
                ),
            ]

            loaded = load_messages(conn, messages)

            assert loaded == 2
            assert get_loaded_message_count(conn) == 2
        finally:
            conn.close()

    def test_ignore_duplicate_behavior(self, empty_analysis_db: Path):
        """Loading same message twice should ignore duplicate."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            message = Message(
                rowid=1,
                chat_id=1,
                handle_id=1,
                text="Hello!",
                date_utc="2024-01-15T10:00:00Z",
                date_local=None,
                is_from_me=False,
            )

            # Load twice
            load_messages(conn, [message])
            loaded = load_messages(conn, [message])

            # Second load should report 0 new
            assert loaded == 0
            # But still only 1 message in DB
            assert get_loaded_message_count(conn) == 1
        finally:
            conn.close()

    def test_empty_list(self, empty_analysis_db: Path):
        """Empty list should return 0."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            loaded = load_messages(conn, [])
            assert loaded == 0
        finally:
            conn.close()

    def test_message_with_null_text(self, empty_analysis_db: Path):
        """Messages with NULL text should load successfully."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            message = Message(
                rowid=1,
                chat_id=1,
                handle_id=1,
                text=None,
                date_utc="2024-01-15T10:00:00Z",
                date_local=None,
                is_from_me=False,
            )

            loaded = load_messages(conn, [message])
            assert loaded == 1
        finally:
            conn.close()


class TestEtlState:
    """Tests for ETL state management."""

    def test_update_and_get_state(self, empty_analysis_db: Path):
        """Should update and retrieve ETL state."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            update_etl_state(conn, "test_key", "test_value")
            value = get_etl_state(conn, "test_key")

            assert value == "test_value"
        finally:
            conn.close()

    def test_update_existing_state(self, empty_analysis_db: Path):
        """Updating existing key should overwrite value."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            update_etl_state(conn, "test_key", "first_value")
            update_etl_state(conn, "test_key", "second_value")

            value = get_etl_state(conn, "test_key")
            assert value == "second_value"
        finally:
            conn.close()

    def test_get_nonexistent_state(self, empty_analysis_db: Path):
        """Getting non-existent key should return None."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            value = get_etl_state(conn, "nonexistent")
            assert value is None
        finally:
            conn.close()

    def test_schema_version_exists(self, empty_analysis_db: Path):
        """Schema version should be set by schema creation."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            value = get_etl_state(conn, "schema_version")
            assert value is not None
        finally:
            conn.close()


class TestGetCounts:
    """Tests for count functions."""

    def test_empty_database_counts(self, empty_analysis_db: Path):
        """Empty database should return zero counts."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            assert get_loaded_handle_count(conn) == 0
            assert get_loaded_message_count(conn) == 0
        finally:
            conn.close()

    def test_counts_after_loading(self, empty_analysis_db: Path):
        """Counts should reflect loaded data."""
        conn = sqlite3.connect(str(empty_analysis_db))
        try:
            # Load handles
            handles = [
                Handle(rowid=i, value_raw=f"+1{i}", value_normalized=f"+1{i}", handle_type="phone")
                for i in range(1, 6)
            ]
            load_handles(conn, handles)

            # Load messages
            messages = [
                Message(
                    rowid=i,
                    chat_id=1,
                    handle_id=1,
                    text=f"Message {i}",
                    date_utc="2024-01-15T10:00:00Z",
                    date_local=None,
                    is_from_me=False,
                )
                for i in range(1, 11)
            ]
            load_messages(conn, messages)

            assert get_loaded_handle_count(conn) == 5
            assert get_loaded_message_count(conn) == 10
        finally:
            conn.close()


class TestLinkMessagesToPersons:
    """Tests for linking messages to persons."""

    def test_links_messages(self, populated_analysis_db: Path):
        """Should link messages to persons based on handle."""
        conn = sqlite3.connect(str(populated_analysis_db))
        try:
            # The populated fixture already has some linked messages
            # Add an unlinked message
            conn.execute(
                """INSERT INTO fact_message 
                   (message_id, chat_id, date_utc, is_from_me, handle_id, text, created_at) 
                   VALUES (100, 1, '2024-01-15T12:00:00Z', 0, 1, 'Unlinked', '2024-01-01')"""
            )
            conn.commit()

            # Link messages
            linked = link_messages_to_persons(conn)

            # Should have linked the new message
            assert linked >= 1
        finally:
            conn.close()

    def test_no_double_linking(self, populated_analysis_db: Path):
        """Already-linked messages should not be re-linked."""
        conn = sqlite3.connect(str(populated_analysis_db))
        try:
            # First link
            link_messages_to_persons(conn)

            # Second link should find nothing to do
            linked = link_messages_to_persons(conn)
            assert linked == 0
        finally:
            conn.close()
