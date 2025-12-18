"""
Tests for analysis.py functions.

Tests the high-level analysis functions that operate on the database.
"""

from unittest.mock import MagicMock, patch
from typing import List, Tuple, Any

import pytest

from imessage_analysis.analysis import (
    get_latest_messages_data,
    get_message_statistics_by_chat,
    get_chat_analysis,
    get_all_contacts_data,
    get_database_summary,
    get_contact_detail,
    get_contact_stats,
    get_contact_chats_data,
)


@pytest.fixture
def mock_db():
    """Create a mock DatabaseConnection."""
    db = MagicMock()
    db.execute_query = MagicMock()
    db.get_table_names = MagicMock()
    db.get_row_counts_by_table = MagicMock()
    return db


class TestGetLatestMessagesData:
    """Tests for get_latest_messages_data function."""

    def test_returns_list(self, mock_db):
        """Should return a list of messages."""
        mock_db.execute_query.return_value = []
        result = get_latest_messages_data(mock_db, limit=10)
        assert isinstance(result, list)

    def test_message_structure(self, mock_db):
        """Each message should have expected keys."""
        mock_db.execute_query.return_value = [
            ("2024-01-15 10:00:00", "Hello", 0, "+14155551234", "John Doe", 1),
        ]
        result = get_latest_messages_data(mock_db, limit=10)

        assert len(result) == 1
        msg = result[0]
        assert "date" in msg
        assert "text" in msg
        assert "is_from_me" in msg
        assert "chat_identifier" in msg
        assert "display_name" in msg
        assert "handle_id" in msg

    def test_is_from_me_conversion(self, mock_db):
        """is_from_me should be converted to boolean."""
        mock_db.execute_query.return_value = [
            ("2024-01-15 10:00:00", "Hello", 1, "+14155551234", "John", 1),
            ("2024-01-15 10:01:00", "Hi", 0, "+14155551234", "John", 1),
        ]
        result = get_latest_messages_data(mock_db, limit=10)

        assert result[0]["is_from_me"] is True
        assert result[1]["is_from_me"] is False

    def test_limit_passed_to_query(self, mock_db):
        """Limit parameter should be passed to query function."""
        mock_db.execute_query.return_value = []
        get_latest_messages_data(mock_db, limit=25)

        # Verify execute_query was called
        mock_db.execute_query.assert_called_once()

    def test_empty_result(self, mock_db):
        """Should handle empty query result."""
        mock_db.execute_query.return_value = []
        result = get_latest_messages_data(mock_db, limit=10)
        assert result == []


class TestGetMessageStatisticsByChat:
    """Tests for get_message_statistics_by_chat function."""

    def test_returns_list(self, mock_db):
        """Should return a list of statistics."""
        mock_db.execute_query.return_value = []
        result = get_message_statistics_by_chat(mock_db)
        assert isinstance(result, list)

    def test_stat_structure(self, mock_db):
        """Each stat should have expected keys."""
        mock_db.execute_query.return_value = [
            ("+14155551234", "John Doe", 150),
        ]
        result = get_message_statistics_by_chat(mock_db)

        assert len(result) == 1
        stat = result[0]
        assert "chat_identifier" in stat
        assert "display_name" in stat
        assert "message_count" in stat

    def test_multiple_chats(self, mock_db):
        """Should handle multiple chat statistics."""
        mock_db.execute_query.return_value = [
            ("+14155551234", "John Doe", 150),
            ("+14155555678", "Jane Smith", 200),
            ("group@imessage.com", "Family", 500),
        ]
        result = get_message_statistics_by_chat(mock_db)
        assert len(result) == 3


class TestGetChatAnalysis:
    """Tests for get_chat_analysis function."""

    def test_returns_dict(self, mock_db):
        """Should return a dictionary."""
        mock_db.execute_query.return_value = []
        result = get_chat_analysis(mock_db, "+14155551234")
        assert isinstance(result, dict)

    def test_analysis_structure(self, mock_db):
        """Analysis should have expected structure."""
        mock_db.execute_query.return_value = []
        result = get_chat_analysis(mock_db, "+14155551234")

        assert "chat_identifier" in result
        assert "from_me" in result
        assert "from_others" in result

    def test_from_me_stats(self, mock_db):
        """Should populate from_me statistics."""
        mock_db.execute_query.return_value = [
            (100, 5000, 2, 1),  # message_count, char_count, pages, is_from_me=1
        ]
        result = get_chat_analysis(mock_db, "+14155551234")

        assert result["from_me"]["message_count"] == 100
        assert result["from_me"]["character_count"] == 5000
        assert result["from_me"]["estimated_pages"] == 2

    def test_from_others_stats(self, mock_db):
        """Should populate from_others statistics."""
        mock_db.execute_query.return_value = [
            (50, 2500, 1, 0),  # message_count, char_count, pages, is_from_me=0
        ]
        result = get_chat_analysis(mock_db, "+14155551234")

        assert result["from_others"]["message_count"] == 50
        assert result["from_others"]["character_count"] == 2500

    def test_percentage_calculation(self, mock_db):
        """Should calculate percentages correctly."""
        mock_db.execute_query.return_value = [
            (75, 3000, 1, 1),  # from_me
            (25, 1000, 0, 0),  # from_others
        ]
        result = get_chat_analysis(mock_db, "+14155551234")

        assert result["from_me"]["percentage"] == 75.0
        assert result["from_others"]["percentage"] == 25.0

    def test_percentage_with_zero_messages(self, mock_db):
        """Should handle zero messages without division error."""
        mock_db.execute_query.return_value = []
        result = get_chat_analysis(mock_db, "+14155551234")

        # Should not have percentage keys when no messages
        assert "percentage" not in result["from_me"]
        assert "percentage" not in result["from_others"]


class TestGetAllContactsData:
    """Tests for get_all_contacts_data function."""

    def test_returns_list(self, mock_db):
        """Should return a list of contacts."""
        mock_db.execute_query.return_value = []
        result = get_all_contacts_data(mock_db)
        assert isinstance(result, list)

    def test_contact_structure(self, mock_db):
        """Each contact should have expected keys."""
        mock_db.execute_query.return_value = [
            (1, "+14155551234", "US", "iMessage", None, None, 150, "John Doe"),
        ]
        result = get_all_contacts_data(mock_db)

        assert len(result) == 1
        contact = result[0]
        assert "rowid" in contact
        assert "id" in contact
        assert "country" in contact
        assert "service" in contact
        assert "uncanonicalized_id" in contact
        assert "person_centric_id" in contact
        assert "message_count" in contact
        assert "display_name" in contact

    def test_multiple_contacts(self, mock_db):
        """Should handle multiple contacts."""
        mock_db.execute_query.return_value = [
            (1, "+14155551234", "US", "iMessage", None, None, 150, "John Doe"),
            (2, "user@example.com", None, "iMessage", None, None, 50, "Jane Smith"),
            (3, "+442071234567", "GB", "iMessage", None, None, 200, "Bob Wilson"),
        ]
        result = get_all_contacts_data(mock_db)
        assert len(result) == 3


class TestGetDatabaseSummary:
    """Tests for get_database_summary function."""

    def test_returns_dict(self, mock_db):
        """Should return a dictionary."""
        mock_db.get_table_names.return_value = []
        mock_db.get_row_counts_by_table.return_value = []
        result = get_database_summary(mock_db)
        assert isinstance(result, dict)

    def test_summary_structure(self, mock_db):
        """Summary should have expected keys."""
        mock_db.get_table_names.return_value = []
        mock_db.get_row_counts_by_table.return_value = []
        result = get_database_summary(mock_db)

        assert "table_count" in result
        assert "tables" in result
        assert "total_messages" in result
        assert "total_chats" in result

    def test_table_count(self, mock_db):
        """Should count tables correctly."""
        mock_db.get_table_names.return_value = ["message", "chat", "handle"]
        mock_db.get_row_counts_by_table.return_value = [
            ("message", 1000),
            ("chat", 50),
            ("handle", 100),
        ]
        result = get_database_summary(mock_db)

        assert result["table_count"] == 3

    def test_message_count_extraction(self, mock_db):
        """Should extract message count from tables dict."""
        mock_db.get_table_names.return_value = ["message", "chat"]
        mock_db.get_row_counts_by_table.return_value = [
            ("message", 12345),
            ("chat", 100),
        ]
        result = get_database_summary(mock_db)

        assert result["total_messages"] == 12345

    def test_chat_count_extraction(self, mock_db):
        """Should extract chat count from tables dict."""
        mock_db.get_table_names.return_value = ["message", "chat"]
        mock_db.get_row_counts_by_table.return_value = [
            ("message", 12345),
            ("chat", 100),
        ]
        result = get_database_summary(mock_db)

        assert result["total_chats"] == 100

    def test_missing_message_table(self, mock_db):
        """Should handle missing message table gracefully."""
        mock_db.get_table_names.return_value = ["chat"]
        mock_db.get_row_counts_by_table.return_value = [("chat", 100)]
        result = get_database_summary(mock_db)

        assert result["total_messages"] == 0


class TestGetContactDetail:
    """Tests for get_contact_detail function."""

    def test_returns_contact_when_found(self, mock_db):
        """Should return contact dictionary when found."""
        mock_db.execute_query.return_value = [
            (1, "+14155551234", "US", "iMessage", None, "person_123"),
        ]
        result = get_contact_detail(mock_db, "+14155551234")

        assert result is not None
        assert result["id"] == "+14155551234"
        assert result["rowid"] == 1
        assert result["country"] == "US"
        assert result["service"] == "iMessage"

    def test_returns_none_when_not_found(self, mock_db):
        """Should return None when contact not found."""
        mock_db.execute_query.return_value = []
        result = get_contact_detail(mock_db, "unknown")

        assert result is None

    def test_contact_structure(self, mock_db):
        """Contact should have expected keys."""
        mock_db.execute_query.return_value = [
            (1, "+14155551234", "US", "iMessage", "raw_id", "person_123"),
        ]
        result = get_contact_detail(mock_db, "+14155551234")

        assert "rowid" in result
        assert "id" in result
        assert "country" in result
        assert "service" in result
        assert "uncanonicalized_id" in result
        assert "person_centric_id" in result


class TestGetContactStats:
    """Tests for get_contact_stats function."""

    def test_returns_dict(self, mock_db):
        """Should return a dictionary."""
        mock_db.execute_query.return_value = []
        result = get_contact_stats(mock_db, "+14155551234")
        assert isinstance(result, dict)

    def test_stats_structure(self, mock_db):
        """Stats should have expected structure."""
        mock_db.execute_query.return_value = []
        result = get_contact_stats(mock_db, "+14155551234")

        assert "handle_id" in result
        assert "from_me" in result
        assert "from_them" in result
        assert "total_messages" in result
        assert "total_characters" in result

    def test_from_me_stats(self, mock_db):
        """Should populate from_me statistics."""
        # row format: message_count, character_count, is_from_me, first_message, last_message
        mock_db.execute_query.return_value = [
            (100, 5000, 1, "2024-01-01", "2024-01-15"),
        ]
        result = get_contact_stats(mock_db, "+14155551234")

        assert result["from_me"]["message_count"] == 100
        assert result["from_me"]["character_count"] == 5000
        assert result["from_me"]["first_message"] == "2024-01-01"
        assert result["from_me"]["last_message"] == "2024-01-15"

    def test_from_them_stats(self, mock_db):
        """Should populate from_them statistics."""
        mock_db.execute_query.return_value = [
            (50, 2500, 0, "2024-01-02", "2024-01-14"),
        ]
        result = get_contact_stats(mock_db, "+14155551234")

        assert result["from_them"]["message_count"] == 50
        assert result["from_them"]["character_count"] == 2500

    def test_both_directions(self, mock_db):
        """Should handle both from_me and from_them."""
        mock_db.execute_query.return_value = [
            (60, 3000, 1, "2024-01-01", "2024-01-15"),  # from_me
            (40, 2000, 0, "2024-01-02", "2024-01-14"),  # from_them
        ]
        result = get_contact_stats(mock_db, "+14155551234")

        assert result["from_me"]["message_count"] == 60
        assert result["from_them"]["message_count"] == 40
        assert result["total_messages"] == 100
        assert result["total_characters"] == 5000

    def test_percentage_calculation(self, mock_db):
        """Should calculate percentages correctly."""
        mock_db.execute_query.return_value = [
            (75, 3750, 1, "2024-01-01", "2024-01-15"),
            (25, 1250, 0, "2024-01-02", "2024-01-14"),
        ]
        result = get_contact_stats(mock_db, "+14155551234")

        assert result["from_me"]["percentage"] == 75.0
        assert result["from_them"]["percentage"] == 25.0

    def test_empty_stats(self, mock_db):
        """Should handle empty query result."""
        mock_db.execute_query.return_value = []
        result = get_contact_stats(mock_db, "+14155551234")

        assert result["total_messages"] == 0
        assert result["total_characters"] == 0
        assert result["from_me"]["message_count"] == 0
        assert result["from_them"]["message_count"] == 0


class TestGetContactChatsData:
    """Tests for get_contact_chats_data function."""

    def test_returns_list(self, mock_db):
        """Should return a list of chats."""
        mock_db.execute_query.return_value = []
        result = get_contact_chats_data(mock_db, "+14155551234")
        assert isinstance(result, list)

    def test_chat_structure(self, mock_db):
        """Each chat should have expected keys."""
        mock_db.execute_query.return_value = [
            ("chat_123", "Family Chat", 150),
        ]
        result = get_contact_chats_data(mock_db, "+14155551234")

        assert len(result) == 1
        chat = result[0]
        assert "chat_identifier" in chat
        assert "display_name" in chat
        assert "message_count" in chat

    def test_multiple_chats(self, mock_db):
        """Should handle multiple chats."""
        mock_db.execute_query.return_value = [
            ("chat_1", "Family", 150),
            ("chat_2", "Work", 200),
            ("chat_3", None, 50),
        ]
        result = get_contact_chats_data(mock_db, "+14155551234")

        assert len(result) == 3
        assert result[0]["chat_identifier"] == "chat_1"
        assert result[0]["message_count"] == 150
        assert result[2]["display_name"] is None

    def test_empty_result(self, mock_db):
        """Should handle empty query result."""
        mock_db.execute_query.return_value = []
        result = get_contact_chats_data(mock_db, "+14155551234")

        assert result == []
