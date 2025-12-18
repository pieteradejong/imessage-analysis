import pytest

from imessage_analysis.queries import (
    get_latest_messages,
    get_total_messages_by_chat,
    table_names,
    rows_count,
    columns_for_table,
    table_creation_query,
    get_all_contacts,
    get_all_messages,
    get_messages_fuzzy_match,
    get_chars_and_length_by_counterpart,
    get_contact_by_id,
    get_contact_statistics,
    get_contact_chats,
    _require_sqlite_identifier,
)


def test_get_latest_messages_includes_limit():
    q, params = get_latest_messages(limit=12)
    assert "LIMIT ?" in q
    assert params == (12,)


def test_get_total_messages_by_chat_has_group_by():
    q = get_total_messages_by_chat()
    assert "GROUP BY" in q


class TestTableNames:
    """Tests for table_names function."""

    def test_returns_sql_query(self):
        q = table_names()
        assert "sqlite_master" in q
        assert "SELECT" in q


class TestRowsCount:
    """Tests for rows_count function."""

    def test_empty_list_returns_zero(self):
        q = rows_count([])
        assert q == "SELECT 0;"

    def test_single_table(self):
        q = rows_count(["messages"])
        assert "SELECT" in q
        assert "messages" in q

    def test_multiple_tables(self):
        q = rows_count(["messages", "handles", "chats"])
        assert "messages" in q
        assert "handles" in q
        assert "chats" in q


class TestRequireSqliteIdentifier:
    """Tests for _require_sqlite_identifier function."""

    def test_valid_identifier(self):
        result = _require_sqlite_identifier("valid_table", field_name="table")
        assert result == "valid_table"

    def test_invalid_identifier_raises(self):
        with pytest.raises(ValueError, match="Invalid table"):
            _require_sqlite_identifier("invalid;table", field_name="table")

    def test_identifier_with_special_chars_raises(self):
        with pytest.raises(ValueError):
            _require_sqlite_identifier("table--drop", field_name="table")


class TestColumnsForTable:
    """Tests for columns_for_table function."""

    def test_returns_pragma_query(self):
        q = columns_for_table("messages")
        assert "PRAGMA table_info" in q
        assert "messages" in q


class TestTableCreationQuery:
    """Tests for table_creation_query function."""

    def test_returns_sql_query(self):
        q = table_creation_query("messages")
        assert "sqlite_master" in q
        assert "SELECT" in q


class TestGetAllContacts:
    """Tests for get_all_contacts function."""

    def test_returns_sql_query(self):
        q = get_all_contacts()
        assert "SELECT" in q
        assert "handle" in q


class TestGetAllMessages:
    """Tests for get_all_messages function."""

    def test_returns_sql_query(self):
        q = get_all_messages()
        assert "SELECT" in q
        assert "message" in q


class TestGetMessagesFuzzyMatch:
    """Tests for get_messages_fuzzy_match function."""

    def test_returns_query_and_params(self):
        q, params = get_messages_fuzzy_match("hello")
        assert "LIKE ?" in q
        assert params == ("%hello%",)


class TestGetCharsAndLengthByCounterpart:
    """Tests for get_chars_and_length_by_counterpart function."""

    def test_returns_query_and_params(self):
        q, params = get_chars_and_length_by_counterpart("+14155551234")
        assert "SELECT" in q
        assert "GROUP BY" in q
        assert params == ("+14155551234",)


class TestGetContactById:
    """Tests for get_contact_by_id function."""

    def test_returns_query_and_params(self):
        q, params = get_contact_by_id("+14155551234")
        assert "SELECT" in q
        assert "handle" in q
        assert params == ("+14155551234",)


class TestGetContactStatistics:
    """Tests for get_contact_statistics function."""

    def test_returns_query_and_params(self):
        q, params = get_contact_statistics("+14155551234")
        assert "SELECT" in q
        assert "COUNT" in q
        assert params == ("+14155551234",)


class TestGetContactChats:
    """Tests for get_contact_chats function."""

    def test_returns_query_and_params(self):
        q, params = get_contact_chats("+14155551234")
        assert "SELECT" in q
        assert "chat" in q
        assert params == ("+14155551234",)
