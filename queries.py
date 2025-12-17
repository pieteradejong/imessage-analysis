import re

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


def table_names() -> str:
    return f"SELECT `name` FROM `sqlite_master` WHERE `type`='table';"


# TODO finish function
def rows_count(table_names: list) -> str:
    # query draft:
    # select ( select count(*) from handle)
    #        ( select count(*) from message)
    #        ( select count(*) from ...etc...);
    if not table_names:
        return "SELECT 0;"
    query: str = f"SELECT "
    for tn in table_names[:-1]:
        safe_tn = _require_sqlite_identifier(tn, field_name="table_name")
        query += f"(SELECT count(*) FROM `{safe_tn}`), "
    safe_last = _require_sqlite_identifier(table_names[-1], field_name="table_name")
    query += f"(SELECT count(*) FROM `{safe_last}`);"
    return query


# TODO verify function semantics
def get_db_size(table_name: str) -> int:
    return f"SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"


def columns_for_table_q(table_name: str) -> str:
    safe_table = _require_sqlite_identifier(table_name, field_name="table_name")
    return f"SELECT `name` FROM pragma_table_info('{safe_table}');"


def table_creation_query(table_name: str) -> str:
    # Use parameterized query for table_name (SQLite supports this for WHERE clauses)
    return "SELECT `sql` FROM sqlite_master WHERE `tbl_name`=? AND `type`='table';"


# TODO fill in query
def get_all_contacts() -> str:
    return f";"


# Query verified to work in SQLite DB Browser, unclear what precisely it does.
ALL_YOUR_MESSAGES: str = f"""
        SELECT
            datetime (message.date / 1000000000 + strftime ("%s", "2001-01-01"), "unixepoch", "localtime") AS message_date,
            message.text,
            message.is_from_me,
            chat.chat_identifier
        FROM
            chat
        JOIN 
            chat_message_join ON chat.ROWID = chat_message_join.chat_id
        JOIN 
            message ON chat_message_join.message_id = message.ROWID
        ORDER BY
            message_date ASC;
    """

# Query verified to work in SQLite DB Browser, unclear what precisely it does.
YOUR_MESSAGES_FUZZY_MATCH_UNICODE_STRING: str = f"""
        SELECT
            datetime (message.date / 1000000000 + strftime ("%s", "2001-01-01"), "unixepoch", "localtime") AS message_date,
            message.text,
            message.is_from_me,
            chat.chat_identifier
        FROM
            chat
            JOIN chat_message_join ON chat. "ROWID" = chat_message_join.chat_id
            JOIN message ON chat_message_join.message_id = message."ROWID"
        WHERE
            message.text like '%😂%'
        ORDER BY
            message_date ASC;
"""

# Query verified to work in SQLite DB Browser, unclear what precisely it does.
TOTAL_MESSAGES_BY_CHAT: str = f"""
        SELECT
            chat.chat_identifier,
            count(chat.chat_identifier) AS message_count
        FROM
            chat
            JOIN chat_message_join ON chat. "ROWID" = chat_message_join.chat_id
            JOIN message ON chat_message_join.message_id = message."ROWID"
        GROUP BY
            chat.chat_identifier
        ORDER BY
            message_count DESC;
"""

# Query verified to not error in SQLite DB Browser, unclear what precisely it does.
CHARS_AND_CHAT_TOTAL_LENGTH_BY_COUNTERPART: str = f"""
        SELECT
            count(*) AS message_count,
            sum(length(message.text)) AS character_count,
            sum(length(message.text)) / 3000 AS estimated_page_count, -- not sure where I got this number, but it seems reasonable
            message.is_from_me
        FROM
            chat
            JOIN chat_message_join ON chat. "ROWID" = chat_message_join.chat_id
            JOIN message ON chat_message_join.message_id = message."ROWID"
        WHERE
            chat.chat_identifier = 'fill in identifier'
        GROUP BY
            message.is_from_me;
"""
