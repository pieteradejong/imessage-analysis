from imessage_analysis.queries import get_latest_messages, get_total_messages_by_chat


def test_get_latest_messages_includes_limit():
    q = get_latest_messages(limit=12)
    assert "LIMIT 12" in q


def test_get_total_messages_by_chat_has_group_by():
    q = get_total_messages_by_chat()
    assert "GROUP BY" in q

