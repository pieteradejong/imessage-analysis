"""
SQL query definitions for iMessage analysis.

Contains reusable SQL query strings for common operations.
"""

import re
from typing import Any, List, Tuple


def table_names() -> str:
    """Get query to retrieve all table names."""
    return "SELECT `name` FROM `sqlite_master` WHERE `type`='table';"


_SQLITE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _require_sqlite_identifier(value: str, *, field_name: str) -> str:
    """
    Validate an identifier (e.g. table name) to prevent SQL injection.

    SQLite does not support binding identifiers as parameters, so we must validate
    before safely interpolating into SQL.
    """
    if not _SQLITE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value


def rows_count(table_names: List[str]) -> str:
    """
    Generate query to get row counts for multiple tables.

    Args:
        table_names: List of table names.

    Returns:
        SQL query string.
    """
    if not table_names:
        return "SELECT 0;"

    query = "SELECT "
    for tn in table_names[:-1]:
        safe_tn = _require_sqlite_identifier(tn, field_name="table_name")
        query += f"(SELECT COUNT(*) FROM `{safe_tn}`), "
    safe_last = _require_sqlite_identifier(table_names[-1], field_name="table_name")
    query += f"(SELECT COUNT(*) FROM `{safe_last}`);"
    return query


def columns_for_table(table_name: str) -> str:
    """
    Get query to retrieve column information for a table.

    Args:
        table_name: Name of the table.

    Returns:
        SQL query string.
    """
    safe_table = _require_sqlite_identifier(table_name, field_name="table_name")
    return f"PRAGMA table_info('{safe_table}');"


def table_creation_query(table_name: str) -> str:
    """
    Get query to retrieve CREATE TABLE statement for a table.

    Args:
        table_name: Name of the table.

    Returns:
        SQL query string.
    """
    return "SELECT `sql` FROM sqlite_master WHERE `tbl_name`=? AND `type`='table';"


def get_all_contacts() -> str:
    """
    Get query to retrieve all contacts (handles) with message counts and display names.

    Returns:
        SQL query string.
    """
    return """
        SELECT 
            h.ROWID,
            h.id,
            h.country,
            h.service,
            h.uncanonicalized_id,
            h.person_centric_id,
            COUNT(DISTINCT m.ROWID) as message_count,
            (
                SELECT c.display_name 
                FROM chat c
                JOIN chat_handle_join chj ON c.ROWID = chj.chat_id
                WHERE chj.handle_id = h.ROWID AND c.display_name IS NOT NULL AND c.display_name != ''
                LIMIT 1
            ) as display_name
        FROM handle h
        LEFT JOIN message m ON m.handle_id = h.ROWID
        GROUP BY h.ROWID
        ORDER BY message_count DESC, h.id;
    """


def get_latest_messages(limit: int = 10) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to retrieve the latest messages.

    Args:
        limit: Number of messages to retrieve.

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT
            datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS message_date,
            message.text,
            message.is_from_me,
            chat.chat_identifier,
            chat.display_name,
            handle.id AS handle_id
        FROM
            chat
        JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message.ROWID
        LEFT JOIN handle ON message.handle_id = handle.ROWID
        ORDER BY message.date DESC
        LIMIT ?;
    """
    return query, (int(limit),)


def get_all_messages() -> str:
    """
    Get query to retrieve all messages.

    Returns:
        SQL query string.
    """
    return """
        SELECT
            datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS message_date,
            message.text,
            message.is_from_me,
            chat.chat_identifier
        FROM
            chat
        JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message.ROWID
        ORDER BY message_date ASC;
    """


def get_messages_fuzzy_match(search_term: str) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to search messages by text content (fuzzy match).

    Args:
        search_term: Text to search for (will be used with LIKE).

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT
            datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS message_date,
            message.text,
            message.is_from_me,
            chat.chat_identifier
        FROM
            chat
        JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message.ROWID
        WHERE
            message.text LIKE ?
        ORDER BY message_date ASC;
    """
    return query, (f"%{search_term}%",)


def get_total_messages_by_chat() -> str:
    """
    Get query to count total messages per chat.

    Returns:
        SQL query string.
    """
    return """
        SELECT
            chat.chat_identifier,
            chat.display_name,
            COUNT(chat.chat_identifier) AS message_count
        FROM
            chat
        JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message.ROWID
        GROUP BY chat.chat_identifier, chat.display_name
        ORDER BY message_count DESC;
    """


def get_chars_and_length_by_counterpart(chat_identifier: str) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to analyze message count and character count by counterpart.

    Args:
        chat_identifier: Chat identifier to filter by.

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT
            COUNT(*) AS message_count,
            SUM(LENGTH(message.text)) AS character_count,
            SUM(LENGTH(message.text)) / 3000.0 AS estimated_page_count,
            message.is_from_me
        FROM
            chat
        JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message.ROWID
        WHERE
            chat.chat_identifier = ?
        GROUP BY message.is_from_me;
    """
    return query, (chat_identifier,)


def get_contact_by_id(handle_id: str) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to retrieve a specific contact by their handle id.

    Args:
        handle_id: The handle identifier (e.g., phone number or email).

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT 
            ROWID,
            id,
            country,
            service,
            uncanonicalized_id,
            person_centric_id
        FROM handle
        WHERE id = ?;
    """
    return query, (handle_id,)


def get_contact_statistics(handle_id: str) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to retrieve message statistics for a specific contact.

    Args:
        handle_id: The handle identifier (e.g., phone number or email).

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT
            COUNT(*) AS message_count,
            SUM(LENGTH(message.text)) AS character_count,
            message.is_from_me,
            MIN(datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime")) AS first_message,
            MAX(datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime")) AS last_message
        FROM message
        JOIN handle ON message.handle_id = handle.ROWID
        WHERE handle.id = ?
        GROUP BY message.is_from_me;
    """
    return query, (handle_id,)


def get_contact_chats(handle_id: str) -> Tuple[str, Tuple[Any, ...]]:
    """
    Get query to retrieve all chats a contact participates in.

    Args:
        handle_id: The handle identifier.

    Returns:
        (SQL query string, parameters tuple).
    """
    query = """
        SELECT DISTINCT
            chat.chat_identifier,
            chat.display_name,
            COUNT(message.ROWID) AS message_count
        FROM chat
        JOIN chat_handle_join ON chat.ROWID = chat_handle_join.chat_id
        JOIN handle ON chat_handle_join.handle_id = handle.ROWID
        LEFT JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
        LEFT JOIN message ON chat_message_join.message_id = message.ROWID
        WHERE handle.id = ?
        GROUP BY chat.chat_identifier, chat.display_name
        ORDER BY message_count DESC;
    """
    return query, (handle_id,)
