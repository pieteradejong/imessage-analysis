"""
ETL Loaders for analysis.db.

This module loads extracted and normalized data into the analysis database.
All operations are designed to be idempotent (safe to run multiple times).

Design Decisions:
    1. Use INSERT OR REPLACE for upsert semantics
    2. Batch inserts for performance
    3. Track ETL state for incremental sync
    4. Preserve original values alongside normalized ones

See LEARNINGS.md for detailed rationale.
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import List, Optional
import logging

import uuid
from typing import Dict, Tuple

from imessage_analysis.etl.extractors import Handle, Message, Contact, ContactPhone, ContactEmail
from imessage_analysis.etl.normalizers import normalize_phone, normalize_email

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Get current UTC timestamp in ISO-8601 format."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_handles(conn: sqlite3.Connection, handles: List[Handle]) -> int:
    """
    Load handles into dim_handle table.

    Uses INSERT OR REPLACE for upsert semantics - existing handles
    will be updated, new ones inserted.

    Args:
        conn: SQLite connection to analysis.db.
        handles: List of Handle objects to load.

    Returns:
        Number of handles loaded.
    """
    if not handles:
        return 0

    now = _now_iso()

    query = """
        INSERT OR REPLACE INTO dim_handle 
            (handle_id, value_raw, value_normalized, handle_type, person_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, 
            (SELECT person_id FROM dim_handle WHERE handle_id = ?),
            COALESCE((SELECT created_at FROM dim_handle WHERE handle_id = ?), ?),
            ?);
    """

    with closing(conn.cursor()) as cursor:
        for handle in handles:
            cursor.execute(
                query,
                (
                    handle.rowid,
                    handle.value_raw,
                    handle.value_normalized,
                    handle.handle_type,
                    handle.rowid,  # For person_id subquery
                    handle.rowid,  # For created_at COALESCE subquery
                    now,  # created_at if new
                    now,  # updated_at always
                ),
            )

        conn.commit()

    logger.info(f"Loaded {len(handles)} handles into dim_handle")
    return len(handles)


def load_messages(conn: sqlite3.Connection, messages: List[Message]) -> int:
    """
    Load messages into fact_message table.

    Uses INSERT OR IGNORE to avoid duplicates - messages with existing
    message_id will be skipped. Handle IDs that don't exist in dim_handle
    are set to NULL to avoid foreign key violations.

    Args:
        conn: SQLite connection to analysis.db.
        messages: List of Message objects to load.

    Returns:
        Number of new messages loaded.
    """
    if not messages:
        return 0

    now = _now_iso()

    # First, get the set of valid handle_ids from dim_handle
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT handle_id FROM dim_handle;")
        valid_handle_ids = {row[0] for row in cursor.fetchall()}

    query = """
        INSERT OR IGNORE INTO fact_message 
            (message_id, chat_id, date_utc, date_local, is_from_me, 
             handle_id, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """

    loaded = 0
    with closing(conn.cursor()) as cursor:
        for message in messages:
            # Only use handle_id if it exists in dim_handle, otherwise NULL
            handle_id = message.handle_id
            if handle_id is not None and handle_id not in valid_handle_ids:
                handle_id = None

            cursor.execute(
                query,
                (
                    message.rowid,
                    message.chat_id,
                    message.date_utc,
                    message.date_local,
                    1 if message.is_from_me else 0,
                    handle_id,
                    message.text,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                loaded += 1

        conn.commit()

    logger.info(
        f"Loaded {loaded} new messages into fact_message (skipped {len(messages) - loaded} duplicates)"
    )
    return loaded


def update_etl_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    """
    Update or insert an ETL state value.

    Args:
        conn: SQLite connection to analysis.db.
        key: State key (e.g., 'last_message_date', 'last_sync').
        value: State value.
    """
    now = _now_iso()

    query = """
        INSERT OR REPLACE INTO etl_state (key, value, updated_at)
        VALUES (?, ?, ?);
    """

    with closing(conn.cursor()) as cursor:
        cursor.execute(query, (key, value, now))
        conn.commit()

    logger.debug(f"Updated ETL state: {key} = {value}")


def get_etl_state(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """
    Get an ETL state value.

    Args:
        conn: SQLite connection to analysis.db.
        key: State key to retrieve.

    Returns:
        State value, or None if not found.
    """
    query = "SELECT value FROM etl_state WHERE key = ?;"

    with closing(conn.cursor()) as cursor:
        cursor.execute(query, (key,))
        result = cursor.fetchone()
        return result[0] if result else None


def get_loaded_message_count(conn: sqlite3.Connection) -> int:
    """
    Get total message count in analysis.db.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of messages in fact_message table.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM fact_message;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_loaded_handle_count(conn: sqlite3.Connection) -> int:
    """
    Get total handle count in analysis.db.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of handles in dim_handle table.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_handle;")
        result = cursor.fetchone()
        return result[0] if result else 0


def link_messages_to_persons(conn: sqlite3.Connection) -> int:
    """
    Update fact_message.person_id based on dim_handle.person_id.

    This denormalizes person_id into the fact table for faster queries.
    Should be called after identity resolution.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of messages updated.
    """
    query = """
        UPDATE fact_message
        SET person_id = (
            SELECT dim_handle.person_id 
            FROM dim_handle 
            WHERE dim_handle.handle_id = fact_message.handle_id
        )
        WHERE handle_id IS NOT NULL
        AND person_id IS NULL;
    """

    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        updated = cursor.rowcount
        conn.commit()

    logger.info(f"Linked {updated} messages to persons")
    return updated


# =============================================================================
# Contacts Database Loading Functions
# =============================================================================


def _generate_person_id() -> str:
    """Generate a new UUID for a person."""
    return str(uuid.uuid4())


def _build_display_name(contact: Contact) -> str:
    """
    Build a display name from contact fields.

    Priority:
        1. First + Last name
        2. First name only
        3. Last name only
        4. Organization
        5. Nickname
        6. "Unknown Contact"
    """
    if contact.first_name and contact.last_name:
        return f"{contact.first_name} {contact.last_name}"
    if contact.first_name:
        return contact.first_name
    if contact.last_name:
        return contact.last_name
    if contact.organization:
        return contact.organization
    if contact.nickname:
        return contact.nickname
    return "Unknown Contact"


def load_persons_from_contacts(
    conn: sqlite3.Connection,
    contacts: List[Contact],
) -> Tuple[int, Dict[int, str]]:
    """
    Load contacts into dim_person table with source='contacts'.

    Creates a new person for each contact, generating UUIDs as person_ids.

    Args:
        conn: SQLite connection to analysis.db.
        contacts: List of Contact objects to load.

    Returns:
        Tuple of (number of persons loaded, mapping of contact_pk → person_id).
    """
    if not contacts:
        return 0, {}

    now = _now_iso()
    contact_to_person: Dict[int, str] = {}

    query = """
        INSERT INTO dim_person 
            (person_id, first_name, last_name, display_name, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'contacts', ?, ?);
    """

    with closing(conn.cursor()) as cursor:
        for contact in contacts:
            person_id = _generate_person_id()
            display_name = _build_display_name(contact)

            cursor.execute(
                query,
                (
                    person_id,
                    contact.first_name,
                    contact.last_name,
                    display_name,
                    now,
                    now,
                ),
            )

            contact_to_person[contact.pk] = person_id

        conn.commit()

    logger.info(f"Loaded {len(contacts)} persons from contacts into dim_person")
    return len(contacts), contact_to_person


def load_contact_methods(
    conn: sqlite3.Connection,
    phones: List[ContactPhone],
    emails: List[ContactEmail],
    contact_to_person: Dict[int, str],
) -> int:
    """
    Load phone numbers and emails into dim_contact_method table.

    Normalizes values and links them to persons via contact_to_person mapping.

    Args:
        conn: SQLite connection to analysis.db.
        phones: List of ContactPhone objects.
        emails: List of ContactEmail objects.
        contact_to_person: Mapping of contact Z_PK to person_id.

    Returns:
        Number of contact methods loaded.
    """
    now = _now_iso()
    loaded = 0

    query = """
        INSERT OR IGNORE INTO dim_contact_method 
            (method_id, person_id, type, value_raw, value_normalized, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """

    with closing(conn.cursor()) as cursor:
        # Load phone numbers
        for phone in phones:
            person_id = contact_to_person.get(phone.owner_pk)
            if not person_id:
                continue  # Skip orphaned phone numbers

            method_id = _generate_person_id()  # UUID for method
            normalized = normalize_phone(phone.full_number)

            cursor.execute(
                query,
                (
                    method_id,
                    person_id,
                    "phone",
                    phone.full_number,
                    normalized,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                loaded += 1

        # Load email addresses
        for email in emails:
            person_id = contact_to_person.get(email.owner_pk)
            if not person_id:
                continue  # Skip orphaned emails

            method_id = _generate_person_id()  # UUID for method
            normalized = normalize_email(email.address)

            cursor.execute(
                query,
                (
                    method_id,
                    person_id,
                    "email",
                    email.address,
                    normalized,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                loaded += 1

        conn.commit()

    logger.info(f"Loaded {loaded} contact methods into dim_contact_method")
    return loaded


def get_loaded_person_count(conn: sqlite3.Connection) -> int:
    """
    Get total person count in analysis.db.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of persons in dim_person table.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_person;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_loaded_contact_method_count(conn: sqlite3.Connection) -> int:
    """
    Get total contact method count in analysis.db.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of contact methods in dim_contact_method table.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_contact_method;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_contacts_person_count(conn: sqlite3.Connection) -> int:
    """
    Get count of persons with source='contacts'.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of persons from contacts.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_person WHERE source = 'contacts';")
        result = cursor.fetchone()
        return result[0] if result else 0
