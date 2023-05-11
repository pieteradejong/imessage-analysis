def table_names() -> str:
    return f"SELECT `name` FROM `sqlite_master` WHERE `type`='table';"

# TODO finish function
def count_rows_for_table(table_names: list[str]) -> list[(str, int)]:
    # query draft:
    # select ( select count(*) from handle)
    #        ( select count(*) from message)
    #        ( select count(*) from ...etc...);
    query: str = f"SELECT "
    for tn in table_names[:-1]:
        query += f"(SELECT count(*) FROM {tn}), "
    query += f"(SELECT count(*) FROM {table_names[-1]});"
    return query

# TODO verify function semantics
def get_db_size(table_name: str) -> int:
    return f"SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"

def columns_for_table_q(table_name: str) -> str:
    return f"SELECT `name` FROM pragma_table_info('{table_name}');"

def table_creation_query(table_name: str) -> str:
    return f"SELECT `sql` FROM sqlite_master WHERE `tbl_name`='{table_name}' and `type`='table';"

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
