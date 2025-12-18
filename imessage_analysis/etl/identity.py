"""
Identity resolution for ETL.

This module resolves handles (phone numbers, emails) to canonical person
identities. Identity resolution is a *process*, not a simple join.

Design Decisions:
    1. Create "inferred" persons for unresolved handles
    2. Support manual overrides via 'manual' source
    3. Cache resolutions in dim_handle.person_id
    4. Use Contacts data (dim_contact_method) for matching

Resolution Strategy:
    1. Exact match on normalized value (phone/email) in dim_contact_method
    2. Fuzzy phone match (last 10 digits) as fallback
    3. If no match, create inferred person from handle

See DATA_ARCHITECTURE.md section 7 for detailed rationale.
"""

import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    """Get current UTC timestamp in ISO-8601 format."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_person_id() -> str:
    """Generate a new UUID for a person."""
    return str(uuid.uuid4())


def _extract_digits(value: str) -> str:
    """Extract only digits from a string."""
    return re.sub(r"\D", "", value)


def resolve_handle_to_person(
    conn: sqlite3.Connection,
    handle_normalized: str,
    handle_type: str = "unknown",
) -> Optional[str]:
    """
    Attempt to resolve a normalized handle value to an existing person.

    Resolution strategy:
        1. Exact match on dim_contact_method.value_normalized
        2. For phones: fuzzy match on last 10 digits

    Args:
        conn: SQLite connection to analysis.db.
        handle_normalized: Normalized handle value (E.164 phone or lowercase email).
        handle_type: Type of handle ('phone', 'email', 'unknown').

    Returns:
        person_id if found, None otherwise.
    """
    # Strategy 1: Exact match
    exact_query = """
        SELECT person_id 
        FROM dim_contact_method 
        WHERE value_normalized = ?
        LIMIT 1;
    """

    with closing(conn.cursor()) as cursor:
        cursor.execute(exact_query, (handle_normalized,))
        result = cursor.fetchone()
        if result:
            person_id: str = result[0]
            return person_id

    # Strategy 2: Fuzzy phone match (last 10 digits)
    if handle_type == "phone":
        handle_digits = _extract_digits(handle_normalized)
        if len(handle_digits) >= 10:
            last_10 = handle_digits[-10:]

            # Find phone contact methods and compare last 10 digits
            fuzzy_query = """
                SELECT person_id, value_normalized 
                FROM dim_contact_method 
                WHERE type = 'phone';
            """

            with closing(conn.cursor()) as cursor:
                cursor.execute(fuzzy_query)
                for row in cursor.fetchall():
                    matched_person_id: str = row[0]
                    contact_normalized: str = row[1]
                    contact_digits = _extract_digits(contact_normalized)
                    if len(contact_digits) >= 10 and contact_digits[-10:] == last_10:
                        logger.debug(
                            f"Fuzzy phone match: {handle_normalized} → {contact_normalized}"
                        )
                        return matched_person_id

    return None


def create_unknown_person(
    conn: sqlite3.Connection,
    handle_value: str,
    handle_type: str,
) -> str:
    """
    Create a placeholder person for an unresolved handle.

    The person is marked with source='inferred' to indicate it was
    auto-created and may need manual resolution later.

    Args:
        conn: SQLite connection to analysis.db.
        handle_value: The handle value (for display_name).
        handle_type: Type of handle ('phone', 'email', 'unknown').

    Returns:
        The newly created person_id.
    """
    person_id = _generate_person_id()
    now = _now_iso()

    # Create display name from handle
    if handle_type == "phone":
        display_name = f"Unknown ({handle_value})"
    elif handle_type == "email":
        # Use the part before @ as a hint
        local_part = handle_value.split("@")[0] if "@" in handle_value else handle_value
        display_name = f"{local_part} (unresolved)"
    else:
        display_name = (
            f"Unknown ({handle_value[:20]}...)"
            if len(handle_value) > 20
            else f"Unknown ({handle_value})"
        )

    query = """
        INSERT INTO dim_person 
            (person_id, first_name, last_name, display_name, source, created_at, updated_at)
        VALUES (?, NULL, NULL, ?, 'inferred', ?, ?);
    """

    with closing(conn.cursor()) as cursor:
        cursor.execute(query, (person_id, display_name, now, now))
        conn.commit()

    logger.debug(f"Created inferred person: {person_id} for handle: {handle_value}")
    return person_id


def link_handle_to_person(
    conn: sqlite3.Connection,
    handle_id: int,
    person_id: str,
) -> None:
    """
    Link a handle to a person in dim_handle.

    Args:
        conn: SQLite connection to analysis.db.
        handle_id: The handle ROWID.
        person_id: The person UUID.
    """
    now = _now_iso()

    query = """
        UPDATE dim_handle 
        SET person_id = ?, updated_at = ?
        WHERE handle_id = ?;
    """

    with closing(conn.cursor()) as cursor:
        cursor.execute(query, (person_id, now, handle_id))
        conn.commit()


def resolve_all_handles(conn: sqlite3.Connection) -> int:
    """
    Resolve all unlinked handles to persons.

    For each handle without a person_id:
        1. Try to find existing person via contact method match
        2. If not found, create an inferred person
        3. Link the handle to the person

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of handles resolved.
    """
    # Get all unresolved handles
    query = """
        SELECT handle_id, value_normalized, handle_type
        FROM dim_handle
        WHERE person_id IS NULL;
    """

    resolved_count = 0

    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        unresolved = cursor.fetchall()

    for handle_id, value_normalized, handle_type in unresolved:
        # Try to find existing person (with fuzzy matching for phones)
        person_id = resolve_handle_to_person(conn, value_normalized, handle_type)

        if not person_id:
            # Create inferred person
            person_id = create_unknown_person(conn, value_normalized, handle_type)

        # Link handle to person
        link_handle_to_person(conn, handle_id, person_id)
        resolved_count += 1

    logger.info(f"Resolved {resolved_count} handles to persons")
    return resolved_count


def get_unresolved_handle_count(conn: sqlite3.Connection) -> int:
    """
    Get count of handles without person_id.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of unresolved handles.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_handle WHERE person_id IS NULL;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_inferred_person_count(conn: sqlite3.Connection) -> int:
    """
    Get count of auto-created (inferred) persons.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of persons with source='inferred'.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_person WHERE source = 'inferred';")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_contacts_person_count(conn: sqlite3.Connection) -> int:
    """
    Get count of persons from contacts.

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of persons with source='contacts'.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_person WHERE source = 'contacts';")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_handles_linked_to_contacts_count(conn: sqlite3.Connection) -> int:
    """
    Get count of handles linked to persons from contacts (not inferred).

    Args:
        conn: SQLite connection to analysis.db.

    Returns:
        Number of handles resolved to contact-sourced persons.
    """
    query = """
        SELECT COUNT(*) 
        FROM dim_handle h
        JOIN dim_person p ON h.person_id = p.person_id
        WHERE p.source = 'contacts';
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else 0
