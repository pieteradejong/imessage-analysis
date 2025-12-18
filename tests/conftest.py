"""
Pytest fixtures for iMessage Analysis tests.

This module provides shared fixtures for testing the ETL pipeline,
including sample databases with test data.

Fixture Categories:
    1. Database fixtures (sample chat.db, empty analysis.db)
    2. Data fixtures (sample handles, messages)
    3. Real database fixtures (optional, for integration tests)

Design Notes:
    - Fixtures use tmp_path for isolation between tests
    - Sample chat.db mimics Apple's schema structure
    - Real chat.db fixtures are skipped if not available
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

# Apple's epoch: 2001-01-01 00:00:00 UTC
APPLE_EPOCH_OFFSET = 978307200


def _datetime_to_apple_ns(dt: datetime) -> int:
    """Convert datetime to Apple's nanosecond timestamp format."""
    unix_ts = dt.timestamp()
    return int((unix_ts - APPLE_EPOCH_OFFSET) * 1_000_000_000)


# =============================================================================
# Sample chat.db fixtures
# =============================================================================


@pytest.fixture
def sample_chat_db(tmp_path: Path) -> Path:
    """
    Create a minimal chat.db with test data.

    Creates a SQLite database that mimics Apple's chat.db schema
    with sample handles, messages, and chats.

    Returns:
        Path to the sample chat.db file.
    """
    db_path = tmp_path / "chat.db"
    conn = sqlite3.connect(str(db_path))

    try:
        # Create minimal schema matching Apple's chat.db
        conn.executescript(
            """
            CREATE TABLE handle (
                ROWID INTEGER PRIMARY KEY,
                id TEXT NOT NULL,
                service TEXT,
                country TEXT,
                uncanonicalized_id TEXT,
                person_centric_id TEXT
            );

            CREATE TABLE chat (
                ROWID INTEGER PRIMARY KEY,
                chat_identifier TEXT,
                display_name TEXT,
                service_name TEXT
            );

            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY,
                text TEXT,
                handle_id INTEGER,
                date INTEGER,
                is_from_me INTEGER DEFAULT 0
            );

            CREATE TABLE chat_message_join (
                chat_id INTEGER,
                message_id INTEGER,
                PRIMARY KEY (chat_id, message_id)
            );
        """
        )

        # Insert sample handles
        handles = [
            (1, "+14155551234", "iMessage", "us"),
            (2, "+14155555678", "iMessage", "us"),
            (3, "user@example.com", "iMessage", None),
            (4, "+442071234567", "iMessage", "gb"),
            (5, "test@gmail.com", "iMessage", None),
        ]
        conn.executemany(
            "INSERT INTO handle (ROWID, id, service, country) VALUES (?, ?, ?, ?)",
            handles,
        )

        # Insert sample chats
        chats = [
            (1, "+14155551234", "John Doe", "iMessage"),
            (2, "+14155555678", None, "iMessage"),
            (3, "user@example.com", "Jane Smith", "iMessage"),
        ]
        conn.executemany(
            "INSERT INTO chat (ROWID, chat_identifier, display_name, service_name) VALUES (?, ?, ?, ?)",
            chats,
        )

        # Insert sample messages with Apple-formatted timestamps
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        messages = [
            (1, "Hello!", 1, _datetime_to_apple_ns(base_time), 0),
            (2, "Hi there!", None, _datetime_to_apple_ns(base_time), 1),
            (3, "How are you?", 1, _datetime_to_apple_ns(base_time), 0),
            (4, "Good thanks!", None, _datetime_to_apple_ns(base_time), 1),
            (5, "Meeting tomorrow?", 2, _datetime_to_apple_ns(base_time), 0),
            (6, None, 3, _datetime_to_apple_ns(base_time), 0),  # Message without text
            (7, "Email test", 3, _datetime_to_apple_ns(base_time), 0),
        ]
        conn.executemany(
            "INSERT INTO message (ROWID, text, handle_id, date, is_from_me) VALUES (?, ?, ?, ?, ?)",
            messages,
        )

        # Insert chat_message_join entries
        joins = [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (2, 5),
            (3, 6),
            (3, 7),
        ]
        conn.executemany(
            "INSERT INTO chat_message_join (chat_id, message_id) VALUES (?, ?)",
            joins,
        )

        conn.commit()

    finally:
        conn.close()

    return db_path


@pytest.fixture
def empty_chat_db(tmp_path: Path) -> Path:
    """
    Create an empty chat.db with schema but no data.

    Returns:
        Path to the empty chat.db file.
    """
    db_path = tmp_path / "empty_chat.db"
    conn = sqlite3.connect(str(db_path))

    try:
        conn.executescript(
            """
            CREATE TABLE handle (
                ROWID INTEGER PRIMARY KEY,
                id TEXT NOT NULL,
                service TEXT,
                country TEXT
            );

            CREATE TABLE chat (
                ROWID INTEGER PRIMARY KEY,
                chat_identifier TEXT,
                display_name TEXT,
                service_name TEXT
            );

            CREATE TABLE message (
                ROWID INTEGER PRIMARY KEY,
                text TEXT,
                handle_id INTEGER,
                date INTEGER,
                is_from_me INTEGER DEFAULT 0
            );

            CREATE TABLE chat_message_join (
                chat_id INTEGER,
                message_id INTEGER
            );
        """
        )
        conn.commit()

    finally:
        conn.close()

    return db_path


# =============================================================================
# Analysis.db fixtures
# =============================================================================


@pytest.fixture
def empty_analysis_db(tmp_path: Path) -> Path:
    """
    Create an empty analysis.db with schema.

    Returns:
        Path to the empty analysis.db file.
    """
    from imessage_analysis.etl.schema import create_schema

    db_path = tmp_path / "analysis.db"
    create_schema(db_path)
    return db_path


@pytest.fixture
def populated_analysis_db(empty_analysis_db: Path) -> Path:
    """
    Create an analysis.db with sample dimension and fact data.

    Returns:
        Path to the populated analysis.db file.
    """
    conn = sqlite3.connect(str(empty_analysis_db))

    try:
        now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Insert sample persons
        persons = [
            ("person-1", "John", "Doe", "John Doe", "inferred", now, now),
            ("person-2", "Jane", "Smith", "Jane Smith", "inferred", now, now),
        ]
        conn.executemany(
            """INSERT INTO dim_person 
               (person_id, first_name, last_name, display_name, source, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            persons,
        )

        # Insert sample handles
        handles = [
            (1, "+14155551234", "+14155551234", "phone", "person-1", now, now),
            (2, "+14155555678", "+14155555678", "phone", "person-2", now, now),
            (3, "user@example.com", "user@example.com", "email", None, now, now),
        ]
        conn.executemany(
            """INSERT INTO dim_handle 
               (handle_id, value_raw, value_normalized, handle_type, person_id, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            handles,
        )

        # Insert sample messages
        messages = [
            (1, 1, "2024-01-15T10:00:00Z", None, 0, 1, "person-1", "Hello!", now),
            (2, 1, "2024-01-15T10:01:00Z", None, 1, None, None, "Hi there!", now),
            (3, 1, "2024-01-15T10:02:00Z", None, 0, 1, "person-1", "How are you?", now),
        ]
        conn.executemany(
            """INSERT INTO fact_message 
               (message_id, chat_id, date_utc, date_local, is_from_me, handle_id, person_id, text, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            messages,
        )

        conn.commit()

    finally:
        conn.close()

    return empty_analysis_db


# =============================================================================
# Real database fixtures (for integration tests)
# =============================================================================


@pytest.fixture
def real_chat_db() -> Optional[Path]:
    """
    Return path to real chat.db if available and accessible.

    This fixture is for integration tests that need to run against
    actual iMessage data. Tests using this fixture should be marked
    with @pytest.mark.integration.

    Returns:
        Path to real chat.db, or skips test if not available/accessible.
    """
    path = Path.home() / "Library" / "Messages" / "chat.db"
    if not path.exists():
        pytest.skip("Real chat.db not available")

    # Also verify we can actually open it (may fail due to permissions)
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.execute("SELECT 1 FROM message LIMIT 1")
        conn.close()
    except sqlite3.OperationalError:
        pytest.skip("Cannot access chat.db (permission denied or locked)")

    return path


@pytest.fixture
def real_analysis_db(tmp_path: Path) -> Path:
    """
    Return path for a temporary analysis.db for integration tests.

    This creates a fresh analysis.db in a temp directory for each test,
    ensuring tests don't interfere with each other or with any existing
    analysis.db.

    Returns:
        Path to temporary analysis.db.
    """
    return tmp_path / "real_analysis.db"


# =============================================================================
# Contacts Database (AddressBook) fixtures
# =============================================================================


@pytest.fixture
def sample_contacts_db(tmp_path: Path) -> Path:
    """
    Create a minimal AddressBook database with Core Data schema.

    Mimics Apple's Contacts database structure with Z-prefixed tables.

    Returns:
        Path to the sample contacts database.
    """
    db_path = tmp_path / "AddressBook-v22.abcddb"
    conn = sqlite3.connect(str(db_path))

    try:
        # Create Core Data schema (simplified)
        conn.executescript(
            """
            -- Contact records
            CREATE TABLE ZABCDRECORD (
                Z_PK INTEGER PRIMARY KEY,
                ZFIRSTNAME TEXT,
                ZLASTNAME TEXT,
                ZORGANIZATION TEXT,
                ZNICKNAME TEXT
            );

            -- Phone numbers
            CREATE TABLE ZABCDPHONENUMBER (
                Z_PK INTEGER PRIMARY KEY,
                ZOWNER INTEGER,
                ZFULLNUMBER TEXT,
                ZLABEL TEXT
            );

            -- Email addresses
            CREATE TABLE ZABCDEMAILADDRESS (
                Z_PK INTEGER PRIMARY KEY,
                ZOWNER INTEGER,
                ZADDRESS TEXT,
                ZLABEL TEXT
            );
        """
        )

        # Insert sample contacts
        contacts = [
            (1, "John", "Doe", None, None),
            (2, "Jane", "Smith", "Acme Corp", None),
            (3, None, None, "Apple Inc", None),  # Organization only
            (4, "Bob", None, None, "Bobby"),  # First name + nickname
        ]
        conn.executemany(
            "INSERT INTO ZABCDRECORD (Z_PK, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION, ZNICKNAME) VALUES (?, ?, ?, ?, ?)",
            contacts,
        )

        # Insert phone numbers
        phones = [
            (1, 1, "+1 (415) 555-1234", "_$!<Mobile>!$_"),
            (2, 1, "+1 (415) 555-5678", "_$!<Home>!$_"),
            (3, 2, "+442079460958", "_$!<Work>!$_"),
            (4, 3, "(800) 275-2273", "_$!<Main>!$_"),  # Apple support
        ]
        conn.executemany(
            "INSERT INTO ZABCDPHONENUMBER (Z_PK, ZOWNER, ZFULLNUMBER, ZLABEL) VALUES (?, ?, ?, ?)",
            phones,
        )

        # Insert email addresses
        emails = [
            (1, 1, "john.doe@example.com", "_$!<Home>!$_"),
            (2, 2, "jane.smith@acme.com", "_$!<Work>!$_"),
            (3, 2, "jane@personal.com", "_$!<Home>!$_"),
        ]
        conn.executemany(
            "INSERT INTO ZABCDEMAILADDRESS (Z_PK, ZOWNER, ZADDRESS, ZLABEL) VALUES (?, ?, ?, ?)",
            emails,
        )

        conn.commit()

    finally:
        conn.close()

    return db_path


@pytest.fixture
def empty_contacts_db(tmp_path: Path) -> Path:
    """
    Create an empty AddressBook database with schema but no data.

    Returns:
        Path to the empty contacts database.
    """
    db_path = tmp_path / "empty_contacts.abcddb"
    conn = sqlite3.connect(str(db_path))

    try:
        conn.executescript(
            """
            CREATE TABLE ZABCDRECORD (
                Z_PK INTEGER PRIMARY KEY,
                ZFIRSTNAME TEXT,
                ZLASTNAME TEXT,
                ZORGANIZATION TEXT,
                ZNICKNAME TEXT
            );

            CREATE TABLE ZABCDPHONENUMBER (
                Z_PK INTEGER PRIMARY KEY,
                ZOWNER INTEGER,
                ZFULLNUMBER TEXT,
                ZLABEL TEXT
            );

            CREATE TABLE ZABCDEMAILADDRESS (
                Z_PK INTEGER PRIMARY KEY,
                ZOWNER INTEGER,
                ZADDRESS TEXT,
                ZLABEL TEXT
            );
        """
        )
        conn.commit()

    finally:
        conn.close()

    return db_path


@pytest.fixture
def real_contacts_db() -> Optional[Path]:
    """
    Return path to real AddressBook if available.

    Requires Full Disk Access on macOS. Skips test if not accessible.

    Returns:
        Path to real contacts database, or skips test if not available.
    """
    # Find the AddressBook database
    addressbook_dir = Path.home() / "Library" / "Application Support" / "AddressBook"

    if not addressbook_dir.exists():
        pytest.skip("AddressBook directory not found")

    # Look for AddressBook-vXX.abcddb files
    for db_file in addressbook_dir.glob("AddressBook-*.abcddb"):
        # Try to open it to verify access
        try:
            conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
            conn.execute("SELECT 1 FROM ZABCDRECORD LIMIT 1")
            conn.close()
            return db_file
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            continue

    pytest.skip("Contacts DB not accessible (Full Disk Access required)")
    return None


# =============================================================================
# Helper fixtures
# =============================================================================


@pytest.fixture
def sample_handles():
    """
    Return a list of sample handle data for testing.

    Returns:
        List of (raw_value, expected_normalized, expected_type) tuples.
    """
    return [
        ("+14155551234", "+14155551234", "phone"),
        ("(415) 555-1234", "+14155551234", "phone"),
        ("415-555-1234", "+14155551234", "phone"),
        ("+1 415 555 1234", "+14155551234", "phone"),
        ("+442071234567", "+442071234567", "phone"),
        ("user@example.com", "user@example.com", "email"),
        ("User@Example.COM", "user@example.com", "email"),
        ("  test@gmail.com  ", "test@gmail.com", "email"),
    ]


@pytest.fixture
def sample_phones():
    """
    Return sample phone numbers with expected normalizations.

    Returns:
        List of (raw, expected_normalized) tuples.
    """
    return [
        ("+14155551234", "+14155551234"),
        ("(415) 555-1234", "+14155551234"),
        ("415-555-1234", "+14155551234"),
        ("415.555.1234", "+14155551234"),
        ("+1 (415) 555-1234", "+14155551234"),
        ("+442079460958", "+442079460958"),
        ("+44 20 7946 0958", "+442079460958"),
    ]


@pytest.fixture
def sample_emails():
    """
    Return sample emails with expected normalizations.

    Returns:
        List of (raw, expected_normalized) tuples.
    """
    return [
        ("user@example.com", "user@example.com"),
        ("User@Example.COM", "user@example.com"),
        ("  test@gmail.com  ", "test@gmail.com"),
        ("UPPERCASE@DOMAIN.ORG", "uppercase@domain.org"),
    ]
