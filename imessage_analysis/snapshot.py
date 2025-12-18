"""
Snapshot utilities for iMessage Analysis.

Provides helpers to create and manage timestamped, consistent SQLite snapshots
of chat.db. The ETL pipeline works exclusively from snapshots, never touching
the original database directly.

Snapshot Strategy:
    1. Before ETL runs, check if a recent snapshot exists
    2. If no snapshot or snapshot is too old, create a new one
    3. ETL reads from the snapshot, not the original chat.db
    4. This ensures safety, consistency, and reproducibility

See DATA_ARCHITECTURE.md for the full architecture.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SnapshotResult:
    """Result of creating a database snapshot."""

    source_path: Path
    snapshot_path: Path
    created_at: datetime


@dataclass(frozen=True)
class SnapshotInfo:
    """Information about an existing snapshot."""

    path: Path
    created_at: datetime
    source_stem: str

    @property
    def age_days(self) -> float:
        """Get the age of the snapshot in days."""
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / (24 * 60 * 60)


# Pattern to parse snapshot filenames: chat_YYYYmmdd_HHMMSS.db
_SNAPSHOT_PATTERN = re.compile(r"^(.+)_(\d{8})_(\d{6})\.db$")


def _default_snapshot_filename(source: Path, created_at: datetime) -> str:
    """Generate default snapshot filename from source and timestamp."""
    # chat.db -> chat_YYYYmmdd_HHMMSS.db
    ts = created_at.strftime("%Y%m%d_%H%M%S")
    suffix = source.suffix if source.suffix else ".db"
    stem = source.stem if source.stem else "chat"
    return f"{stem}_{ts}{suffix}"


def _parse_snapshot_filename(filename: str) -> Optional[SnapshotInfo]:
    """
    Parse a snapshot filename to extract metadata.

    Args:
        filename: Snapshot filename (e.g., 'chat_20250115_103045.db')

    Returns:
        SnapshotInfo if filename matches pattern, None otherwise.
    """
    match = _SNAPSHOT_PATTERN.match(filename)
    if not match:
        return None

    source_stem = match.group(1)
    date_str = match.group(2)
    time_str = match.group(3)

    try:
        created_at = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        return SnapshotInfo(
            path=Path(filename),  # Will be updated with full path by caller
            created_at=created_at,
            source_stem=source_stem,
        )
    except ValueError:
        return None


def list_snapshots(snapshots_dir: Path, source_stem: str = "chat") -> List[SnapshotInfo]:
    """
    List all snapshots in a directory, sorted by creation date (newest first).

    Args:
        snapshots_dir: Directory containing snapshots.
        source_stem: Filter to snapshots from this source (default: 'chat').

    Returns:
        List of SnapshotInfo objects, sorted newest first.
    """
    snapshots_dir = Path(snapshots_dir).expanduser().resolve()

    if not snapshots_dir.exists():
        return []

    snapshots: List[SnapshotInfo] = []
    for f in snapshots_dir.iterdir():
        if not f.is_file():
            continue

        info = _parse_snapshot_filename(f.name)
        if info and info.source_stem == source_stem:
            # Update path to full path
            snapshots.append(
                SnapshotInfo(
                    path=f,
                    created_at=info.created_at,
                    source_stem=info.source_stem,
                )
            )

    # Sort by creation date, newest first
    snapshots.sort(key=lambda s: s.created_at, reverse=True)
    return snapshots


def get_latest_snapshot(snapshots_dir: Path, source_stem: str = "chat") -> Optional[SnapshotInfo]:
    """
    Get the most recent snapshot for a source.

    Args:
        snapshots_dir: Directory containing snapshots.
        source_stem: Filter to snapshots from this source (default: 'chat').

    Returns:
        SnapshotInfo for the newest snapshot, or None if no snapshots exist.
    """
    snapshots = list_snapshots(snapshots_dir, source_stem)
    return snapshots[0] if snapshots else None


def snapshot_needs_refresh(
    snapshots_dir: Path,
    max_age_days: int = 7,
    source_stem: str = "chat",
) -> bool:
    """
    Check if a new snapshot is needed.

    A new snapshot is needed if:
    - No snapshots exist, OR
    - The newest snapshot is older than max_age_days

    Args:
        snapshots_dir: Directory containing snapshots.
        max_age_days: Maximum age in days before refresh is needed.
        source_stem: Filter to snapshots from this source (default: 'chat').

    Returns:
        True if a new snapshot should be created, False otherwise.
    """
    latest = get_latest_snapshot(snapshots_dir, source_stem)
    if latest is None:
        return True

    return latest.age_days > max_age_days


def create_timestamped_snapshot(
    source_db_path: Path,
    snapshots_dir: Path,
    *,
    snapshot_name: Optional[str] = None,
) -> SnapshotResult:
    """
    Create a consistent, timestamped snapshot of a SQLite database.

    This uses SQLite's backup API, which avoids problems with copying only the
    main file when the source database is in WAL mode.

    Args:
        source_db_path: Path to the source SQLite database (e.g., chat.db).
        snapshots_dir: Directory where snapshots will be written.
        snapshot_name: Optional explicit filename for the snapshot.

    Returns:
        SnapshotResult with the snapshot path.
    """
    source_db_path = Path(source_db_path).expanduser().resolve()
    snapshots_dir = Path(snapshots_dir).expanduser().resolve()

    created_at = datetime.now()
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    snapshot_filename = snapshot_name or _default_snapshot_filename(source_db_path, created_at)
    snapshot_path = (snapshots_dir / snapshot_filename).resolve()

    source_uri = f"file:{source_db_path}?mode=ro"

    logger.info(f"Creating snapshot: {snapshot_path}")
    with closing(sqlite3.connect(source_uri, uri=True)) as src_conn:
        with closing(sqlite3.connect(str(snapshot_path))) as dst_conn:
            src_conn.backup(dst_conn)

    logger.info(f"Snapshot created successfully: {snapshot_path}")
    return SnapshotResult(
        source_path=source_db_path,
        snapshot_path=snapshot_path,
        created_at=created_at,
    )


def get_or_create_snapshot(
    source_db_path: Path,
    snapshots_dir: Path,
    max_age_days: int = 7,
    force_new: bool = False,
) -> Path:
    """
    Get an existing snapshot or create a new one if needed.

    This is the main entry point for the snapshot-first ETL strategy.
    It returns a path to a snapshot that can be used for ETL processing.

    Args:
        source_db_path: Path to the source database (e.g., chat.db).
        snapshots_dir: Directory for storing snapshots.
        max_age_days: Maximum age of snapshots before creating a new one.
        force_new: If True, always create a new snapshot.

    Returns:
        Path to the snapshot to use for processing.

    Raises:
        FileNotFoundError: If source_db_path doesn't exist.
        PermissionError: If source database can't be read.
    """
    source_db_path = Path(source_db_path).expanduser().resolve()
    snapshots_dir = Path(snapshots_dir).expanduser().resolve()

    if not source_db_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_db_path}")

    source_stem = source_db_path.stem

    # Check if we need a new snapshot
    needs_new = force_new or snapshot_needs_refresh(snapshots_dir, max_age_days, source_stem)

    if needs_new:
        logger.info(f"Creating new snapshot (force={force_new}, max_age={max_age_days} days)")
        result = create_timestamped_snapshot(source_db_path, snapshots_dir)
        return result.snapshot_path
    else:
        latest = get_latest_snapshot(snapshots_dir, source_stem)
        if latest:
            logger.info(
                f"Using existing snapshot: {latest.path.name} " f"(age: {latest.age_days:.1f} days)"
            )
            return latest.path
        else:
            # Shouldn't happen, but handle gracefully
            logger.warning("No existing snapshot found, creating new one")
            result = create_timestamped_snapshot(source_db_path, snapshots_dir)
            return result.snapshot_path


def cleanup_old_snapshots(
    snapshots_dir: Path,
    keep_count: int = 3,
    source_stem: str = "chat",
) -> List[Path]:
    """
    Remove old snapshots, keeping only the most recent ones.

    Args:
        snapshots_dir: Directory containing snapshots.
        keep_count: Number of recent snapshots to keep.
        source_stem: Filter to snapshots from this source (default: 'chat').

    Returns:
        List of paths that were deleted.
    """
    snapshots = list_snapshots(snapshots_dir, source_stem)
    deleted: List[Path] = []

    # Keep the newest `keep_count` snapshots
    for snapshot in snapshots[keep_count:]:
        try:
            snapshot.path.unlink()
            deleted.append(snapshot.path)
            logger.info(f"Deleted old snapshot: {snapshot.path.name}")
        except OSError as e:
            logger.warning(f"Failed to delete snapshot {snapshot.path}: {e}")

    return deleted
