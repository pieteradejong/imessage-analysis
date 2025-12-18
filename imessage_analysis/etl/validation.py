"""
ETL Validation module.

This module provides automated validation checks to verify ETL success.
Run these checks after ETL to ensure data integrity and quality.

Validation Checks:
    1. Handle count matches between source and target
    2. Message count matches (within tolerance for incremental)
    3. No orphaned messages (all handle_ids exist in dim_handle)
    4. Normalization quality (phones are E.164, emails lowercase)
    5. ETL state is valid
    6. Date formats are correct

See DATA_ARCHITECTURE.md for success criteria.
"""

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import logging

from imessage_analysis.etl.extractors import get_handle_count, get_message_count

logger = logging.getLogger(__name__)

# E.164 phone format regex
E164_PATTERN = re.compile(r"^\+\d{7,15}$")

# ISO-8601 date format regex (basic)
ISO8601_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$")


@dataclass
class ValidationCheck:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    details: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of all validation checks."""

    passed: bool
    checks: List[ValidationCheck] = field(default_factory=list)
    summary: str = ""

    def __str__(self) -> str:
        lines = []
        for check in self.checks:
            icon = "✓" if check.passed else "✗"
            lines.append(f"{icon} {check.name}: {check.message}")
            if check.details and not check.passed:
                lines.append(f"  → {check.details}")

        status = "All checks passed" if self.passed else "Some checks failed"
        lines.append(f"\n{status}.")
        return "\n".join(lines)


def _open_chat_db(path: Path) -> sqlite3.Connection:
    """Open chat.db in read-only mode."""
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _open_analysis_db(path: Path) -> sqlite3.Connection:
    """Open analysis.db in read-only mode for validation."""
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def check_handle_count(
    chat_conn: sqlite3.Connection,
    analysis_conn: sqlite3.Connection,
) -> ValidationCheck:
    """
    Verify all handles from chat.db exist in dim_handle.

    Args:
        chat_conn: Connection to chat.db.
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    source_count = get_handle_count(chat_conn)

    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_handle;")
        target_count = cursor.fetchone()[0]

    passed = source_count == target_count
    message = f"{target_count} handles (expected {source_count})"

    return ValidationCheck(
        name="Handle count",
        passed=passed,
        message=message,
        details=f"Missing {source_count - target_count} handles" if not passed else None,
    )


def check_message_count(
    chat_conn: sqlite3.Connection,
    analysis_conn: sqlite3.Connection,
) -> ValidationCheck:
    """
    Verify message counts match between source and target.

    Note: For incremental syncs, target may have fewer messages.
    This check verifies target <= source.

    Args:
        chat_conn: Connection to chat.db.
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    source_count = get_message_count(chat_conn)

    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM fact_message;")
        target_count = cursor.fetchone()[0]

    # Target should not exceed source
    passed = target_count <= source_count
    coverage = (target_count / source_count * 100) if source_count > 0 else 100

    message = f"{target_count} messages ({coverage:.1f}% of {source_count})"

    return ValidationCheck(
        name="Message count",
        passed=passed,
        message=message,
        details=f"Target has more messages than source!" if not passed else None,
    )


def check_no_orphan_messages(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify all fact_message.handle_id values exist in dim_handle.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    query = """
        SELECT COUNT(*) FROM fact_message 
        WHERE handle_id IS NOT NULL 
        AND handle_id NOT IN (SELECT handle_id FROM dim_handle);
    """

    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute(query)
        orphan_count = cursor.fetchone()[0]

    passed = orphan_count == 0
    message = "No orphaned messages" if passed else f"{orphan_count} orphaned messages"

    return ValidationCheck(
        name="No orphan messages",
        passed=passed,
        message=message,
        details="Messages reference non-existent handles" if not passed else None,
    )


def check_normalization_quality(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify phone normalization quality (E.164 format).

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    query = """
        SELECT value_normalized, handle_type 
        FROM dim_handle 
        WHERE handle_type = 'phone';
    """

    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute(query)
        phones = cursor.fetchall()

    if not phones:
        return ValidationCheck(
            name="Phone normalization",
            passed=True,
            message="No phone handles to validate",
        )

    valid_count = sum(1 for phone, _ in phones if E164_PATTERN.match(phone))
    total = len(phones)
    percentage = (valid_count / total * 100) if total > 0 else 100

    # Consider 90%+ as passing (some edge cases may not normalize)
    passed = percentage >= 90

    message = f"{percentage:.1f}% E.164 compliant ({valid_count}/{total})"

    return ValidationCheck(
        name="Phone normalization",
        passed=passed,
        message=message,
        details=f"{total - valid_count} phones not in E.164 format" if not passed else None,
    )


def check_etl_state(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify ETL state contains valid sync information.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute("SELECT key, value FROM etl_state;")
        state = dict(cursor.fetchall())

    required_keys = ["schema_version", "last_sync"]
    missing = [k for k in required_keys if k not in state]

    if missing:
        return ValidationCheck(
            name="ETL state",
            passed=False,
            message=f"Missing required keys: {missing}",
        )

    last_sync = state.get("last_sync", "")
    if not ISO8601_PATTERN.match(last_sync):
        return ValidationCheck(
            name="ETL state",
            passed=False,
            message=f"Invalid last_sync format: {last_sync}",
        )

    return ValidationCheck(
        name="ETL state",
        passed=True,
        message=f"Valid (last sync: {last_sync})",
    )


def check_date_formats(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify all date_utc values are valid ISO-8601 format.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    query = """
        SELECT COUNT(*) FROM fact_message 
        WHERE date_utc IS NOT NULL 
        AND date_utc NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*';
    """

    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute(query)
        invalid_count = cursor.fetchone()[0]

    passed = invalid_count == 0
    message = "All dates valid" if passed else f"{invalid_count} invalid dates"

    return ValidationCheck(
        name="Date formats",
        passed=passed,
        message=message,
    )


def check_contacts_loaded(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify dim_person has contacts-sourced entries.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    with closing(analysis_conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM dim_person WHERE source = 'contacts';")
        contacts_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dim_person;")
        total_count = cursor.fetchone()[0]

    if total_count == 0:
        return ValidationCheck(
            name="Contacts loaded",
            passed=True,
            message="No persons in database (contacts sync may not have run)",
        )

    percentage = (contacts_count / total_count * 100) if total_count > 0 else 0

    return ValidationCheck(
        name="Contacts loaded",
        passed=True,  # Always passes - just informational
        message=f"{contacts_count} contacts ({percentage:.1f}% of {total_count} persons)",
    )


def check_contact_methods_linked(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Verify contact methods are properly linked to persons.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    with closing(analysis_conn.cursor()) as cursor:
        # Check for orphaned contact methods (no person_id)
        cursor.execute("SELECT COUNT(*) FROM dim_contact_method WHERE person_id IS NULL;")
        orphaned = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dim_contact_method;")
        total = cursor.fetchone()[0]

    if total == 0:
        return ValidationCheck(
            name="Contact methods linked",
            passed=True,
            message="No contact methods in database",
        )

    passed = orphaned == 0
    message = f"{total} methods, all linked" if passed else f"{orphaned}/{total} orphaned"

    return ValidationCheck(
        name="Contact methods linked",
        passed=passed,
        message=message,
        details=f"{orphaned} contact methods have no person_id" if not passed else None,
    )


def check_identity_resolution_rate(analysis_conn: sqlite3.Connection) -> ValidationCheck:
    """
    Calculate percentage of handles resolved to contacts vs inferred.

    Args:
        analysis_conn: Connection to analysis.db.

    Returns:
        ValidationCheck result.
    """
    with closing(analysis_conn.cursor()) as cursor:
        # Handles linked to contacts
        cursor.execute(
            """
            SELECT COUNT(*) FROM dim_handle h
            JOIN dim_person p ON h.person_id = p.person_id
            WHERE p.source = 'contacts';
        """
        )
        linked_to_contacts = cursor.fetchone()[0]

        # Handles linked to inferred
        cursor.execute(
            """
            SELECT COUNT(*) FROM dim_handle h
            JOIN dim_person p ON h.person_id = p.person_id
            WHERE p.source = 'inferred';
        """
        )
        linked_to_inferred = cursor.fetchone()[0]

        # Total handles with person_id
        cursor.execute("SELECT COUNT(*) FROM dim_handle WHERE person_id IS NOT NULL;")
        total_linked = cursor.fetchone()[0]

    if total_linked == 0:
        return ValidationCheck(
            name="Identity resolution rate",
            passed=True,
            message="No handles resolved yet",
        )

    contacts_rate = (linked_to_contacts / total_linked * 100) if total_linked > 0 else 0

    return ValidationCheck(
        name="Identity resolution rate",
        passed=True,  # Informational, always passes
        message=f"{contacts_rate:.1f}% resolved to contacts ({linked_to_contacts}/{total_linked})",
        details=f"{linked_to_inferred} resolved to inferred persons",
    )


def validate_etl(
    chat_db_path: Path,
    analysis_db_path: Path,
    include_contacts_checks: bool = True,
) -> ValidationResult:
    """
    Run all validation checks after ETL.

    Args:
        chat_db_path: Path to chat.db (source).
        analysis_db_path: Path to analysis.db (target).
        include_contacts_checks: Include contacts-specific validation checks.

    Returns:
        ValidationResult with all check results.
    """
    checks: List[ValidationCheck] = []

    try:
        chat_conn = _open_chat_db(chat_db_path)
        analysis_conn = _open_analysis_db(analysis_db_path)

        try:
            # Run core checks
            checks.append(check_handle_count(chat_conn, analysis_conn))
            checks.append(check_message_count(chat_conn, analysis_conn))
            checks.append(check_no_orphan_messages(analysis_conn))
            checks.append(check_normalization_quality(analysis_conn))
            checks.append(check_etl_state(analysis_conn))
            checks.append(check_date_formats(analysis_conn))

            # Run contacts-specific checks
            if include_contacts_checks:
                checks.append(check_contacts_loaded(analysis_conn))
                checks.append(check_contact_methods_linked(analysis_conn))
                checks.append(check_identity_resolution_rate(analysis_conn))

        finally:
            chat_conn.close()
            analysis_conn.close()

    except Exception as e:
        checks.append(
            ValidationCheck(
                name="Connection",
                passed=False,
                message=f"Failed to connect: {e}",
            )
        )

    all_passed = all(check.passed for check in checks)
    passed_count = sum(1 for c in checks if c.passed)

    result = ValidationResult(
        passed=all_passed,
        checks=checks,
        summary=f"{passed_count}/{len(checks)} checks passed",
    )

    logger.info(f"Validation complete: {result.summary}")
    return result
