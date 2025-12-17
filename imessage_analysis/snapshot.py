"""
Snapshot utilities for iMessage Analysis.

Provides helpers to create timestamped, consistent SQLite snapshots of `chat.db`.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SnapshotResult:
    """Result of creating a database snapshot."""

    source_path: Path
    snapshot_path: Path
    created_at: datetime


def _default_snapshot_filename(source: Path, created_at: datetime) -> str:
    # chat.db -> chat_YYYYmmdd_HHMMSS.db
    ts = created_at.strftime("%Y%m%d_%H%M%S")
    suffix = source.suffix if source.suffix else ".db"
    stem = source.stem if source.stem else "chat"
    return f"{stem}_{ts}{suffix}"


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

    with closing(sqlite3.connect(source_uri, uri=True)) as src_conn:
        with closing(sqlite3.connect(str(snapshot_path))) as dst_conn:
            src_conn.backup(dst_conn)

    return SnapshotResult(
        source_path=source_db_path,
        snapshot_path=snapshot_path,
        created_at=created_at,
    )

