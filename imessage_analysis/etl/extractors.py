"""
ETL Extractors for chat.db and Contacts (AddressBook) databases.

This module extracts data from Apple's iMessage database (chat.db) and
Contacts database (AddressBook-vXX.abcddb) in a read-only, schema-defensive manner.

Design Decisions:
    1. We never trust Apple schemas to be stable across macOS versions
    2. All extractions are SELECT-only with explicit column lists
    3. Timestamps are converted to UTC ISO-8601 format immediately
    4. Handles are extracted with both raw and normalized values
    5. Incremental extraction supported via since_date parameter
    6. Contacts DB uses Core Data Z* prefixes - query defensively

See LEARNINGS.md for detailed rationale.
"""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import logging

from imessage_analysis.etl.normalizers import normalize_handle

logger = logging.getLogger(__name__)

# Apple's epoch: 2001-01-01 00:00:00 UTC
# chat.db stores dates as nanoseconds since this epoch
APPLE_EPOCH_OFFSET = 978307200  # seconds between Unix epoch and Apple epoch


@dataclass
class Handle:
    """Extracted handle from chat.db."""

    rowid: int
    value_raw: str
    value_normalized: str
    handle_type: str  # 'phone', 'email', or 'unknown'
    service: Optional[str] = None
    country: Optional[str] = None


@dataclass
class Message:
    """Extracted message from chat.db."""

    rowid: int
    chat_id: Optional[int]
    handle_id: Optional[int]
    text: Optional[str]
    date_utc: str  # ISO-8601 format
    date_local: Optional[str]  # ISO-8601 format
    is_from_me: bool


@dataclass
class Chat:
    """Extracted chat from chat.db."""

    rowid: int
    chat_identifier: str
    display_name: Optional[str]
    service_name: Optional[str]


# =============================================================================
# Contacts Database (AddressBook) Dataclasses
# =============================================================================


@dataclass
class Contact:
    """
    Extracted contact from AddressBook (ZABCDRECORD table).

    Core Data uses Z_PK as primary key, not ROWID.
    """

    pk: int  # Z_PK from Core Data
    first_name: Optional[str]
    last_name: Optional[str]
    organization: Optional[str]
    nickname: Optional[str]


@dataclass
class ContactPhone:
    """
    Phone number linked to a contact (ZABCDPHONENUMBER table).

    The owner_pk links to Contact.pk (ZABCDRECORD.Z_PK).
    """

    pk: int  # Z_PK
    owner_pk: int  # ZOWNER -> ZABCDRECORD.Z_PK
    full_number: str  # ZFULLNUMBER
    label: Optional[str]  # ZLABEL (home, work, mobile, etc.)


@dataclass
class ContactEmail:
    """
    Email address linked to a contact (ZABCDEMAILADDRESS table).

    The owner_pk links to Contact.pk (ZABCDRECORD.Z_PK).
    """

    pk: int  # Z_PK
    owner_pk: int  # ZOWNER -> ZABCDRECORD.Z_PK
    address: str  # ZADDRESS
    label: Optional[str]  # ZLABEL (home, work, etc.)


def _convert_apple_timestamp(nanoseconds: Optional[int]) -> Optional[str]:
    """
    Convert Apple's nanosecond timestamp to ISO-8601 UTC string.

    Args:
        nanoseconds: Nanoseconds since 2001-01-01 00:00:00 UTC.

    Returns:
        ISO-8601 formatted datetime string, or None if input is None/0.
    """
    if not nanoseconds:
        return None

    # Convert nanoseconds to seconds and add Apple epoch offset
    seconds = nanoseconds / 1_000_000_000 + APPLE_EPOCH_OFFSET

    try:
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OSError):
        # Handle out-of-range timestamps
        return None


def extract_handles(conn: sqlite3.Connection) -> List[Handle]:
    """
    Extract all handles from chat.db.

    Args:
        conn: SQLite connection to chat.db (read-only recommended).

    Returns:
        List of Handle objects with normalized values.
    """
    query = """
        SELECT 
            ROWID,
            id,
            service,
            country
        FROM handle
        ORDER BY ROWID;
    """

    handles = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        for row in cursor.fetchall():
            rowid, raw_id, service, country = row

            # Normalize the handle value
            normalized, handle_type = normalize_handle(raw_id or "")

            handles.append(
                Handle(
                    rowid=rowid,
                    value_raw=raw_id or "",
                    value_normalized=normalized,
                    handle_type=handle_type,
                    service=service,
                    country=country,
                )
            )

    logger.info(f"Extracted {len(handles)} handles from chat.db")
    return handles


def extract_messages(
    conn: sqlite3.Connection,
    since_date: Optional[str] = None,
) -> List[Message]:
    """
    Extract messages from chat.db, optionally since a given date.

    Args:
        conn: SQLite connection to chat.db (read-only recommended).
        since_date: Optional ISO-8601 date string. If provided, only messages
                    after this date are extracted (for incremental sync).

    Returns:
        List of Message objects.
    """
    # Base query with chat_message_join to get chat_id
    query = """
        SELECT 
            m.ROWID,
            cmj.chat_id,
            m.handle_id,
            m.text,
            m.date,
            m.is_from_me
        FROM message m
        LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
    """

    params: tuple = ()

    # Add date filter for incremental extraction
    if since_date:
        # Convert ISO-8601 to Apple timestamp
        try:
            dt = datetime.fromisoformat(since_date.replace("Z", "+00:00"))
            unix_ts = dt.timestamp()
            apple_ns = int((unix_ts - APPLE_EPOCH_OFFSET) * 1_000_000_000)
            query += " WHERE m.date > ?"
            params = (apple_ns,)
        except ValueError:
            logger.warning(f"Invalid since_date format: {since_date}, ignoring filter")

    query += " ORDER BY m.date ASC;"

    messages = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        for row in cursor.fetchall():
            rowid, chat_id, handle_id, text, date_ns, is_from_me = row

            date_utc = _convert_apple_timestamp(date_ns)
            if not date_utc:
                # Skip messages without valid dates
                continue

            messages.append(
                Message(
                    rowid=rowid,
                    chat_id=chat_id,
                    handle_id=handle_id,
                    text=text,
                    date_utc=date_utc,
                    date_local=None,  # Could compute with timezone, but UTC is sufficient
                    is_from_me=bool(is_from_me),
                )
            )

    logger.info(f"Extracted {len(messages)} messages from chat.db")
    return messages


def extract_chats(conn: sqlite3.Connection) -> List[Chat]:
    """
    Extract all chats from chat.db.

    Args:
        conn: SQLite connection to chat.db (read-only recommended).

    Returns:
        List of Chat objects.
    """
    query = """
        SELECT 
            ROWID,
            chat_identifier,
            display_name,
            service_name
        FROM chat
        ORDER BY ROWID;
    """

    chats = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        for row in cursor.fetchall():
            rowid, chat_identifier, display_name, service_name = row

            chats.append(
                Chat(
                    rowid=rowid,
                    chat_identifier=chat_identifier or "",
                    display_name=display_name,
                    service_name=service_name,
                )
            )

    logger.info(f"Extracted {len(chats)} chats from chat.db")
    return chats


def get_message_count(conn: sqlite3.Connection) -> int:
    """
    Get total message count from chat.db.

    Args:
        conn: SQLite connection to chat.db.

    Returns:
        Total number of messages.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM message;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_handle_count(conn: sqlite3.Connection) -> int:
    """
    Get total handle count from chat.db.

    Args:
        conn: SQLite connection to chat.db.

    Returns:
        Total number of handles.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM handle;")
        result = cursor.fetchone()
        return result[0] if result else 0


def get_latest_message_date(conn: sqlite3.Connection) -> Optional[str]:
    """
    Get the date of the most recent message in chat.db.

    Args:
        conn: SQLite connection to chat.db.

    Returns:
        ISO-8601 date string of the latest message, or None if no messages.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT MAX(date) FROM message;")
        result = cursor.fetchone()
        if result and result[0]:
            return _convert_apple_timestamp(result[0])
    return None


# =============================================================================
# Contacts Database (AddressBook) Extraction Functions
# =============================================================================


def extract_contacts(conn: sqlite3.Connection) -> List[Contact]:
    """
    Extract all contacts from AddressBook database.

    Queries the ZABCDRECORD table (Core Data entity for contacts).

    Args:
        conn: SQLite connection to AddressBook database (read-only recommended).

    Returns:
        List of Contact objects.
    """
    query = """
        SELECT 
            Z_PK,
            ZFIRSTNAME,
            ZLASTNAME,
            ZORGANIZATION,
            ZNICKNAME
        FROM ZABCDRECORD
        ORDER BY Z_PK;
    """

    contacts = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        for row in cursor.fetchall():
            pk, first_name, last_name, organization, nickname = row

            contacts.append(
                Contact(
                    pk=pk,
                    first_name=first_name,
                    last_name=last_name,
                    organization=organization,
                    nickname=nickname,
                )
            )

    logger.info(f"Extracted {len(contacts)} contacts from AddressBook")
    return contacts


def extract_contact_phones(conn: sqlite3.Connection) -> List[ContactPhone]:
    """
    Extract all phone numbers from AddressBook database.

    Queries the ZABCDPHONENUMBER table.

    Args:
        conn: SQLite connection to AddressBook database (read-only recommended).

    Returns:
        List of ContactPhone objects.
    """
    query = """
        SELECT 
            Z_PK,
            ZOWNER,
            ZFULLNUMBER,
            ZLABEL
        FROM ZABCDPHONENUMBER
        WHERE ZOWNER IS NOT NULL AND ZFULLNUMBER IS NOT NULL
        ORDER BY Z_PK;
    """

    phones = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        for row in cursor.fetchall():
            pk, owner_pk, full_number, label = row

            phones.append(
                ContactPhone(
                    pk=pk,
                    owner_pk=owner_pk,
                    full_number=full_number,
                    label=label,
                )
            )

    logger.info(f"Extracted {len(phones)} phone numbers from AddressBook")
    return phones


def extract_contact_emails(conn: sqlite3.Connection) -> List[ContactEmail]:
    """
    Extract all email addresses from AddressBook database.

    Queries the ZABCDEMAILADDRESS table.

    Args:
        conn: SQLite connection to AddressBook database (read-only recommended).

    Returns:
        List of ContactEmail objects.
    """
    query = """
        SELECT 
            Z_PK,
            ZOWNER,
            ZADDRESS,
            ZLABEL
        FROM ZABCDEMAILADDRESS
        WHERE ZOWNER IS NOT NULL AND ZADDRESS IS NOT NULL
        ORDER BY Z_PK;
    """

    emails = []
    with closing(conn.cursor()) as cursor:
        cursor.execute(query)
        for row in cursor.fetchall():
            pk, owner_pk, address, label = row

            emails.append(
                ContactEmail(
                    pk=pk,
                    owner_pk=owner_pk,
                    address=address,
                    label=label,
                )
            )

    logger.info(f"Extracted {len(emails)} email addresses from AddressBook")
    return emails


def get_contact_count(conn: sqlite3.Connection) -> int:
    """
    Get total contact count from AddressBook.

    Args:
        conn: SQLite connection to AddressBook database.

    Returns:
        Total number of contacts.
    """
    with closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM ZABCDRECORD;")
        result = cursor.fetchone()
        return result[0] if result else 0
