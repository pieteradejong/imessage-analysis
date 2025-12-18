"""
Schema definitions for analysis.db.

This module defines the DDL (Data Definition Language) for the analytical
database that sits between Apple's source databases and your analysis code.

Design Decisions:
    1. Use TEXT UUIDs for person_id to support identity merging without renumbering
    2. Store both raw and normalized values for debugging and audit trails
    3. Use ISO-8601 TEXT for timestamps (SQLite-friendly, human-readable)
    4. Foreign keys are optional (person_id can be NULL until resolved)
    5. etl_state table tracks sync progress for incremental updates

See DATA_ARCHITECTURE.md for the full rationale.
"""

import sqlite3
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)

# Schema version for migration tracking
SCHEMA_VERSION = "1.0.0"

# Table creation DDL with inline documentation
SCHEMA_DDL = """
-- =============================================================================
-- dim_person: Canonical human identity
-- =============================================================================
-- Design decision: Use TEXT UUIDs for person_id to support merging identities
-- later without renumbering. The 'source' field tracks provenance:
--   - 'contacts': Extracted from AddressBook database
--   - 'manual': User-created override
--   - 'inferred': Auto-created from unresolved handle
--
CREATE TABLE IF NOT EXISTS dim_person (
    person_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    display_name TEXT,
    source TEXT NOT NULL DEFAULT 'inferred',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =============================================================================
-- dim_contact_method: Normalized contact methods (phones, emails)
-- =============================================================================
-- Links multiple contact methods to a single person.
-- value_raw preserves the original format; value_normalized is used for matching.
--
CREATE TABLE IF NOT EXISTS dim_contact_method (
    method_id TEXT PRIMARY KEY,
    person_id TEXT REFERENCES dim_person(person_id),
    type TEXT NOT NULL CHECK (type IN ('phone', 'email')),
    value_raw TEXT NOT NULL,
    value_normalized TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contact_method_normalized 
    ON dim_contact_method(value_normalized);

CREATE INDEX IF NOT EXISTS idx_contact_method_person 
    ON dim_contact_method(person_id);

-- =============================================================================
-- dim_handle: Bridges iMessage handles to people
-- =============================================================================
-- Each handle from chat.db maps to one entry here.
-- person_id is NULL until identity resolution links it to a dim_person.
--
CREATE TABLE IF NOT EXISTS dim_handle (
    handle_id INTEGER PRIMARY KEY,
    value_raw TEXT NOT NULL,
    value_normalized TEXT NOT NULL,
    handle_type TEXT NOT NULL CHECK (handle_type IN ('phone', 'email', 'unknown')),
    person_id TEXT REFERENCES dim_person(person_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_handle_normalized 
    ON dim_handle(value_normalized);

CREATE INDEX IF NOT EXISTS idx_handle_person 
    ON dim_handle(person_id);

-- =============================================================================
-- fact_message: Main analytical fact table
-- =============================================================================
-- Denormalized for query performance. Contains the resolved person_id
-- for direct analysis without joins when possible.
--
CREATE TABLE IF NOT EXISTS fact_message (
    message_id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    date_utc TEXT NOT NULL,
    date_local TEXT,
    is_from_me INTEGER NOT NULL CHECK (is_from_me IN (0, 1)),
    handle_id INTEGER REFERENCES dim_handle(handle_id),
    person_id TEXT REFERENCES dim_person(person_id),
    text TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_message_date 
    ON fact_message(date_utc);

CREATE INDEX IF NOT EXISTS idx_message_chat 
    ON fact_message(chat_id);

CREATE INDEX IF NOT EXISTS idx_message_handle 
    ON fact_message(handle_id);

CREATE INDEX IF NOT EXISTS idx_message_person 
    ON fact_message(person_id);

-- =============================================================================
-- etl_state: Track incremental sync progress
-- =============================================================================
-- Key-value store for ETL metadata. Common keys:
--   - 'last_message_date': Latest message date synced (for incremental)
--   - 'last_handle_rowid': Latest handle ROWID synced
--   - 'schema_version': Current schema version
--   - 'last_full_sync': Timestamp of last complete sync
--
CREATE TABLE IF NOT EXISTS etl_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =============================================================================
-- Schema metadata
-- =============================================================================
-- Insert schema version on creation
INSERT OR REPLACE INTO etl_state (key, value, updated_at) 
VALUES ('schema_version', '{schema_version}', datetime('now'));
""".format(
    schema_version=SCHEMA_VERSION
)


def create_schema(db_path: Path) -> None:
    """
    Create the analysis.db schema if it doesn't exist.

    This function is idempotent - safe to call multiple times.
    Uses IF NOT EXISTS for all table and index creation.

    Args:
        db_path: Path to the analysis.db file. Parent directory will be created
                 if it doesn't exist.

    Raises:
        sqlite3.Error: If schema creation fails.
    """
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating/verifying schema at: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        # Enable foreign key enforcement
        conn.execute("PRAGMA foreign_keys = ON;")

        # Execute schema DDL
        conn.executescript(SCHEMA_DDL)
        conn.commit()

        logger.info(f"Schema created/verified successfully (version {SCHEMA_VERSION})")
    except sqlite3.Error as e:
        logger.error(f"Schema creation failed: {e}")
        raise
    finally:
        conn.close()


def get_table_names(db_path: Path) -> List[str]:
    """
    Get all table names in the analysis database.

    Args:
        db_path: Path to the analysis.db file.

    Returns:
        List of table names.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def verify_schema(db_path: Path) -> bool:
    """
    Verify that the schema exists and has all required tables.

    Args:
        db_path: Path to the analysis.db file.

    Returns:
        True if schema is valid, False otherwise.
    """
    required_tables = {
        "dim_person",
        "dim_contact_method",
        "dim_handle",
        "fact_message",
        "etl_state",
    }

    if not db_path.exists():
        return False

    existing_tables = set(get_table_names(db_path))
    return required_tables.issubset(existing_tables)
