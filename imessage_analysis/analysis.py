"""
Analysis functions for iMessage data.

Provides high-level analysis functions for message patterns and statistics.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from imessage_analysis.database import DatabaseConnection
from imessage_analysis.queries import (
    get_latest_messages,
    get_total_messages_by_chat,
    get_chars_and_length_by_counterpart,
    get_all_contacts,
    get_contact_by_id,
    get_contact_statistics,
    get_contact_chats,
)

logger = logging.getLogger(__name__)


def get_latest_messages_data(db: DatabaseConnection, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the latest messages from the database.

    Args:
        db: Database connection.
        limit: Number of messages to retrieve.

    Returns:
        List of message dictionaries with keys: date, text, is_from_me, chat_identifier, display_name, handle_id.
    """
    query, params = get_latest_messages(limit)
    rows = db.execute_query(query, params)

    messages = []
    for row in rows:
        messages.append(
            {
                "date": row[0],
                "text": row[1],
                "is_from_me": bool(row[2]),
                "chat_identifier": row[3],
                "display_name": row[4],
                "handle_id": row[5],
            }
        )

    logger.info(f"Retrieved {len(messages)} latest messages")
    return messages


def get_message_statistics_by_chat(db: DatabaseConnection) -> List[Dict[str, Any]]:
    """
    Get message count statistics grouped by chat.

    Args:
        db: Database connection.

    Returns:
        List of dictionaries with chat_identifier and message_count.
    """
    query = get_total_messages_by_chat()
    rows = db.execute_query(query)

    stats = []
    for row in rows:
        stats.append(
            {
                "chat_identifier": row[0],
                "display_name": row[1],
                "message_count": row[2],
            }
        )

    logger.info(f"Retrieved statistics for {len(stats)} chats")
    return stats


def get_chat_analysis(db: DatabaseConnection, chat_identifier: str) -> Dict[str, Any]:
    """
    Get detailed analysis for a specific chat.

    Args:
        db: Database connection.
        chat_identifier: Chat identifier to analyze.

    Returns:
        Dictionary with message counts, character counts, and other statistics.
    """
    query, params = get_chars_and_length_by_counterpart(chat_identifier)
    rows = db.execute_query(query, params)

    analysis: Dict[str, Any] = {
        "chat_identifier": chat_identifier,
        "from_me": {"message_count": 0, "character_count": 0},
        "from_others": {"message_count": 0, "character_count": 0},
    }

    for row in rows:
        is_from_me = bool(row[3])
        if is_from_me:
            analysis["from_me"] = {
                "message_count": row[0],
                "character_count": row[1],
                "estimated_pages": row[2],
            }
        else:
            analysis["from_others"] = {
                "message_count": row[0],
                "character_count": row[1],
                "estimated_pages": row[2],
            }

    total_messages = analysis["from_me"]["message_count"] + analysis["from_others"]["message_count"]
    if total_messages > 0:
        analysis["from_me"]["percentage"] = (
            analysis["from_me"]["message_count"] / total_messages
        ) * 100
        analysis["from_others"]["percentage"] = (
            analysis["from_others"]["message_count"] / total_messages
        ) * 100

    logger.info(f"Analyzed chat: {chat_identifier}")
    return analysis


def get_all_contacts_data(db: DatabaseConnection) -> List[Dict[str, Any]]:
    """
    Get all contacts (handles) from the database with message counts and display names.

    Args:
        db: Database connection.

    Returns:
        List of contact dictionaries sorted by message count.
    """
    query = get_all_contacts()
    rows = db.execute_query(query)

    contacts = []
    for row in rows:
        contacts.append(
            {
                "rowid": row[0],
                "id": row[1],
                "country": row[2],
                "service": row[3],
                "uncanonicalized_id": row[4],
                "person_centric_id": row[5],
                "message_count": row[6],
                "display_name": row[7],
            }
        )

    logger.info(f"Retrieved {len(contacts)} contacts")
    return contacts


def get_database_summary(db: DatabaseConnection) -> Dict[str, Any]:
    """
    Get a summary of the database contents.

    Args:
        db: Database connection.

    Returns:
        Dictionary with table names, row counts, and other metadata.
    """
    table_names = db.get_table_names()
    row_counts = db.get_row_counts_by_table(table_names)

    summary: Dict[str, Any] = {
        "table_count": len(table_names),
        "tables": {name: count for name, count in row_counts},
        "total_messages": 0,
        "total_chats": 0,
    }

    # Get specific counts for important tables
    if "message" in summary["tables"]:
        summary["total_messages"] = summary["tables"]["message"]
    if "chat" in summary["tables"]:
        summary["total_chats"] = summary["tables"]["chat"]

    logger.info("Generated database summary")
    return summary


def get_contact_detail(db: DatabaseConnection, handle_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific contact.

    Args:
        db: Database connection.
        handle_id: The handle identifier (e.g., phone number or email).

    Returns:
        Dictionary with contact info, or None if not found.
    """
    query, params = get_contact_by_id(handle_id)
    rows = db.execute_query(query, params)

    if not rows:
        return None

    row = rows[0]
    contact = {
        "rowid": row[0],
        "id": row[1],
        "country": row[2],
        "service": row[3],
        "uncanonicalized_id": row[4],
        "person_centric_id": row[5],
    }

    logger.info(f"Retrieved contact detail for: {handle_id}")
    return contact


def get_contact_stats(db: DatabaseConnection, handle_id: str) -> Dict[str, Any]:
    """
    Get message statistics for a specific contact.

    Args:
        db: Database connection.
        handle_id: The handle identifier.

    Returns:
        Dictionary with message statistics.
    """
    query, params = get_contact_statistics(handle_id)
    rows = db.execute_query(query, params)

    stats: Dict[str, Any] = {
        "handle_id": handle_id,
        "from_me": {
            "message_count": 0,
            "character_count": 0,
            "first_message": None,
            "last_message": None,
        },
        "from_them": {
            "message_count": 0,
            "character_count": 0,
            "first_message": None,
            "last_message": None,
        },
        "total_messages": 0,
        "total_characters": 0,
    }

    for row in rows:
        is_from_me = bool(row[2])
        data = {
            "message_count": row[0] or 0,
            "character_count": row[1] or 0,
            "first_message": row[3],
            "last_message": row[4],
        }
        if is_from_me:
            stats["from_me"] = data
        else:
            stats["from_them"] = data

    stats["total_messages"] = (
        stats["from_me"]["message_count"] + stats["from_them"]["message_count"]
    )
    stats["total_characters"] = (
        stats["from_me"]["character_count"] + stats["from_them"]["character_count"]
    )

    # Calculate percentages
    if stats["total_messages"] > 0:
        stats["from_me"]["percentage"] = round(
            (stats["from_me"]["message_count"] / stats["total_messages"]) * 100, 1
        )
        stats["from_them"]["percentage"] = round(
            (stats["from_them"]["message_count"] / stats["total_messages"]) * 100, 1
        )

    logger.info(f"Retrieved statistics for contact: {handle_id}")
    return stats


def get_contact_chats_data(db: DatabaseConnection, handle_id: str) -> List[Dict[str, Any]]:
    """
    Get all chats a contact participates in.

    Args:
        db: Database connection.
        handle_id: The handle identifier.

    Returns:
        List of chat dictionaries.
    """
    query, params = get_contact_chats(handle_id)
    rows = db.execute_query(query, params)

    chats = []
    for row in rows:
        chats.append(
            {
                "chat_identifier": row[0],
                "display_name": row[1],
                "message_count": row[2],
            }
        )

    logger.info(f"Retrieved {len(chats)} chats for contact: {handle_id}")
    return chats
