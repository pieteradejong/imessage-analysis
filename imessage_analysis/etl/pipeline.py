"""
ETL Pipeline orchestration.

This module orchestrates the full ETL flow from chat.db (and optionally
Contacts DB) to analysis.db. It coordinates extraction, transformation,
loading, and identity resolution.

IMPORTANT: Snapshot-First Strategy
    The ETL pipeline NEVER accesses the original chat.db directly.
    Instead, it works from snapshots stored in a dedicated directory.
    This provides:
    - Safety: Original database is never touched
    - Consistency: Analysis runs on a point-in-time copy
    - Reproducibility: Same snapshot yields same results

Pipeline Steps:
    0. Get or create a chat.db snapshot (if needed)
    1. Initialize analysis.db schema (if needed)
    2. Extract handles from snapshot
    3. Load handles into dim_handle
    4. Extract messages (incremental if possible)
    5. Load messages into fact_message
    6. (Optional) Extract contacts from AddressBook
    7. (Optional) Load persons and contact methods
    8. Resolve handles to persons (with contact matching)
    9. Link messages to persons
    10. Update ETL state

See DATA_ARCHITECTURE.md for the full architecture.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import logging

from imessage_analysis.etl.schema import create_schema, verify_schema
from imessage_analysis.etl.extractors import (
    extract_handles,
    extract_messages,
    extract_contacts,
    extract_contact_phones,
    extract_contact_emails,
    get_handle_count,
    get_message_count,
)
from imessage_analysis.etl.loaders import (
    load_handles,
    load_messages,
    load_persons_from_contacts,
    load_contact_methods,
    update_etl_state,
    get_etl_state,
    link_messages_to_persons,
    get_loaded_handle_count,
    get_loaded_message_count,
    get_loaded_person_count,
    get_loaded_contact_method_count,
)
from imessage_analysis.etl.identity import resolve_all_handles
from imessage_analysis.snapshot import get_or_create_snapshot, get_latest_snapshot

logger = logging.getLogger(__name__)


@dataclass
class ETLResult:
    """Result of an ETL run."""

    success: bool
    handles_extracted: int
    handles_loaded: int
    messages_extracted: int
    messages_loaded: int
    handles_resolved: int
    messages_linked: int
    is_incremental: bool
    # Contacts-related metrics
    contacts_extracted: int = 0
    contact_methods_loaded: int = 0
    contacts_synced: bool = False
    # Snapshot information
    snapshot_path: Optional[Path] = None
    snapshot_created: bool = False
    # Error and timing
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else f"FAILED: {self.error}"
        mode = "incremental" if self.is_incremental else "full"
        contacts_info = ""
        if self.contacts_synced:
            contacts_info = f"\n  Contacts: {self.contacts_extracted} extracted, {self.contact_methods_loaded} methods loaded"
        snapshot_info = ""
        if self.snapshot_path:
            action = "created" if self.snapshot_created else "reused"
            snapshot_info = f"\n  Snapshot: {self.snapshot_path.name} ({action})"
        return (
            f"ETL {status} ({mode}){snapshot_info}\n"
            f"  Handles: {self.handles_extracted} extracted, {self.handles_loaded} loaded\n"
            f"  Messages: {self.messages_extracted} extracted, {self.messages_loaded} loaded"
            f"{contacts_info}\n"
            f"  Identity: {self.handles_resolved} handles resolved, {self.messages_linked} messages linked\n"
            f"  Duration: {self.duration_seconds:.2f}s"
        )


def _open_chat_db(path: Path) -> sqlite3.Connection:
    """Open chat.db in read-only mode."""
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _open_analysis_db(path: Path) -> sqlite3.Connection:
    """Open analysis.db in read-write mode."""
    return sqlite3.connect(str(path))


def _open_contacts_db(path: Path) -> Optional[sqlite3.Connection]:
    """
    Open AddressBook database in read-only mode.

    Returns None if the database cannot be accessed (e.g., permission denied).
    """
    try:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        # Test if we can actually query it
        conn.execute("SELECT 1 FROM ZABCDRECORD LIMIT 1")
        return conn
    except sqlite3.OperationalError as e:
        logger.warning(f"Cannot access Contacts DB: {e}")
        return None
    except sqlite3.DatabaseError as e:
        logger.warning(f"Contacts DB error: {e}")
        return None


def run_etl(
    chat_db_path: Path,
    analysis_db_path: Path,
    contacts_db_path: Optional[Path] = None,
    force_full: bool = False,
) -> ETLResult:
    """
    Run the full ETL pipeline.

    Args:
        chat_db_path: Path to chat.db (source).
        analysis_db_path: Path to analysis.db (destination).
        contacts_db_path: Optional path to AddressBook database for contact resolution.
        force_full: If True, ignore incremental state and do full sync.

    Returns:
        ETLResult with statistics and success status.
    """
    start_time = datetime.now()
    is_incremental = False
    contacts_extracted = 0
    contact_methods_loaded = 0
    contacts_synced = False

    try:
        # Step 1: Ensure schema exists
        logger.info("Step 1: Ensuring schema exists...")
        create_schema(analysis_db_path)

        # Open connections
        chat_conn = _open_chat_db(chat_db_path)
        analysis_conn = _open_analysis_db(analysis_db_path)
        contacts_conn: Optional[sqlite3.Connection] = None

        if contacts_db_path:
            contacts_conn = _open_contacts_db(contacts_db_path)
            if contacts_conn:
                logger.info(f"Contacts DB opened: {contacts_db_path}")
            else:
                logger.warning("Contacts DB not accessible, skipping contacts sync")

        try:
            # Enable foreign keys
            analysis_conn.execute("PRAGMA foreign_keys = ON;")

            # Check for incremental sync
            last_message_date = None
            if not force_full:
                last_message_date = get_etl_state(analysis_conn, "last_message_date")
                if last_message_date:
                    is_incremental = True
                    logger.info(f"Incremental sync from: {last_message_date}")

            # Step 2: Extract handles
            logger.info("Step 2: Extracting handles...")
            handles = extract_handles(chat_conn)

            # Step 3: Load handles
            logger.info("Step 3: Loading handles...")
            handles_loaded = load_handles(analysis_conn, handles)

            # Step 4: Extract messages
            logger.info("Step 4: Extracting messages...")
            messages = extract_messages(chat_conn, since_date=last_message_date)

            # Step 5: Load messages
            logger.info("Step 5: Loading messages...")
            messages_loaded = load_messages(analysis_conn, messages)

            # Step 6: Extract and load contacts (if available)
            if contacts_conn:
                logger.info("Step 6: Extracting contacts...")
                contacts = extract_contacts(contacts_conn)
                phones = extract_contact_phones(contacts_conn)
                emails = extract_contact_emails(contacts_conn)

                logger.info("Step 6b: Loading persons from contacts...")
                persons_loaded, contact_to_person = load_persons_from_contacts(
                    analysis_conn, contacts
                )

                logger.info("Step 6c: Loading contact methods...")
                contact_methods_loaded = load_contact_methods(
                    analysis_conn, phones, emails, contact_to_person
                )

                contacts_extracted = len(contacts)
                contacts_synced = True
                update_etl_state(
                    analysis_conn,
                    "last_contacts_sync",
                    datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                )

            # Step 7: Resolve identity (with contact matching if available)
            logger.info("Step 7: Resolving handle identities...")
            handles_resolved = resolve_all_handles(analysis_conn)

            # Step 8: Link messages to persons
            logger.info("Step 8: Linking messages to persons...")
            messages_linked = link_messages_to_persons(analysis_conn)

            # Step 9: Update ETL state
            logger.info("Step 9: Updating ETL state...")
            if messages:
                # Find the latest message date
                latest_date = max(m.date_utc for m in messages)
                update_etl_state(analysis_conn, "last_message_date", latest_date)

            now_iso = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            update_etl_state(analysis_conn, "last_sync", now_iso)

            duration = (datetime.now() - start_time).total_seconds()

            result = ETLResult(
                success=True,
                handles_extracted=len(handles),
                handles_loaded=handles_loaded,
                messages_extracted=len(messages),
                messages_loaded=messages_loaded,
                handles_resolved=handles_resolved,
                messages_linked=messages_linked,
                is_incremental=is_incremental,
                contacts_extracted=contacts_extracted,
                contact_methods_loaded=contact_methods_loaded,
                contacts_synced=contacts_synced,
                duration_seconds=duration,
            )

            logger.info(f"ETL completed successfully in {duration:.2f}s")
            return result

        finally:
            chat_conn.close()
            analysis_conn.close()
            if contacts_conn:
                contacts_conn.close()

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"ETL failed: {e}")
        return ETLResult(
            success=False,
            handles_extracted=0,
            handles_loaded=0,
            messages_extracted=0,
            messages_loaded=0,
            handles_resolved=0,
            messages_linked=0,
            is_incremental=is_incremental,
            error=str(e),
            duration_seconds=duration,
        )


def get_etl_status(analysis_db_path: Path) -> dict:
    """
    Get current ETL status from analysis.db.

    Args:
        analysis_db_path: Path to analysis.db.

    Returns:
        Dictionary with ETL status information.
    """
    if not analysis_db_path.exists():
        return {"exists": False}

    conn = _open_analysis_db(analysis_db_path)
    try:
        return {
            "exists": True,
            "schema_valid": verify_schema(analysis_db_path),
            "handle_count": get_loaded_handle_count(conn),
            "message_count": get_loaded_message_count(conn),
            "person_count": get_loaded_person_count(conn),
            "contact_method_count": get_loaded_contact_method_count(conn),
            "last_sync": get_etl_state(conn, "last_sync"),
            "last_message_date": get_etl_state(conn, "last_message_date"),
            "last_contacts_sync": get_etl_state(conn, "last_contacts_sync"),
            "schema_version": get_etl_state(conn, "schema_version"),
        }
    finally:
        conn.close()


def run_etl_with_snapshot(
    source_db_path: Path,
    analysis_db_path: Path,
    snapshots_dir: Path,
    contacts_db_path: Optional[Path] = None,
    snapshot_max_age_days: int = 7,
    force_full: bool = False,
    force_new_snapshot: bool = False,
) -> ETLResult:
    """
    Run the full ETL pipeline using a snapshot of the source database.

    This is the recommended entry point for ETL. It ensures the original
    chat.db is never accessed directly during ETL processing.

    Snapshot Strategy:
        1. Check if a recent snapshot exists (within snapshot_max_age_days)
        2. If not, create a new snapshot from source_db_path
        3. Run ETL against the snapshot

    Args:
        source_db_path: Path to original chat.db (only used for snapshotting).
        analysis_db_path: Path to analysis.db (destination).
        snapshots_dir: Directory for storing snapshots.
        contacts_db_path: Optional path to AddressBook database.
        snapshot_max_age_days: Maximum age of snapshots before refresh (default: 7).
        force_full: If True, ignore incremental ETL state and do full sync.
        force_new_snapshot: If True, always create a new snapshot.

    Returns:
        ETLResult with statistics and success status.
    """
    start_time = datetime.now()

    # Step 0: Get or create snapshot
    logger.info("Step 0: Ensuring snapshot exists...")

    # Check existing snapshot before creating
    existing_snapshot = get_latest_snapshot(snapshots_dir, source_db_path.stem)
    snapshot_existed = (
        existing_snapshot is not None and existing_snapshot.age_days <= snapshot_max_age_days
    )

    try:
        snapshot_path = get_or_create_snapshot(
            source_db_path=source_db_path,
            snapshots_dir=snapshots_dir,
            max_age_days=snapshot_max_age_days,
            force_new=force_new_snapshot,
        )
        snapshot_created = not snapshot_existed or force_new_snapshot
    except (FileNotFoundError, PermissionError) as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Failed to create/get snapshot: {e}")
        return ETLResult(
            success=False,
            handles_extracted=0,
            handles_loaded=0,
            messages_extracted=0,
            messages_loaded=0,
            handles_resolved=0,
            messages_linked=0,
            is_incremental=False,
            error=f"Snapshot error: {e}",
            duration_seconds=duration,
        )

    logger.info(f"Using snapshot: {snapshot_path}")

    # Run ETL against the snapshot
    result = run_etl(
        chat_db_path=snapshot_path,
        analysis_db_path=analysis_db_path,
        contacts_db_path=contacts_db_path,
        force_full=force_full,
    )

    # Add snapshot information to result
    result.snapshot_path = snapshot_path
    result.snapshot_created = snapshot_created

    return result
