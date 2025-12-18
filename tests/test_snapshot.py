import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from imessage_analysis.snapshot import (
    _default_snapshot_filename,
    _parse_snapshot_filename,
    create_timestamped_snapshot,
    list_snapshots,
    get_latest_snapshot,
    snapshot_needs_refresh,
    get_or_create_snapshot,
    cleanup_old_snapshots,
    SnapshotResult,
    SnapshotInfo,
)


def test_default_snapshot_filename():
    created_at = datetime(2025, 12, 17, 10, 11, 12)
    name = _default_snapshot_filename(Path("chat.db"), created_at)
    assert name == "chat_20251217_101112.db"


def test_default_snapshot_filename_no_suffix():
    """Test filename generation for a database without .db suffix."""
    created_at = datetime(2025, 1, 1, 0, 0, 0)
    name = _default_snapshot_filename(Path("mydb"), created_at)
    assert name == "mydb_20250101_000000.db"


class TestSnapshotResult:
    """Tests for SnapshotResult dataclass."""

    def test_snapshot_result_fields(self):
        """Test that SnapshotResult has correct fields."""
        now = datetime.now()
        result = SnapshotResult(
            source_path=Path("/source/chat.db"),
            snapshot_path=Path("/dest/chat_snapshot.db"),
            created_at=now,
        )
        assert result.source_path == Path("/source/chat.db")
        assert result.snapshot_path == Path("/dest/chat_snapshot.db")
        assert result.created_at == now

    def test_snapshot_result_is_frozen(self):
        """Test that SnapshotResult is immutable."""
        result = SnapshotResult(
            source_path=Path("/source/chat.db"),
            snapshot_path=Path("/dest/chat_snapshot.db"),
            created_at=datetime.now(),
        )
        with pytest.raises(AttributeError):
            result.source_path = Path("/new/path")


class TestCreateTimestampedSnapshot:
    """Tests for create_timestamped_snapshot function."""

    def test_creates_snapshot(self, tmp_path: Path):
        """Test that snapshot is created successfully."""
        # Create a source database
        source_db = tmp_path / "source" / "chat.db"
        source_db.parent.mkdir(parents=True)
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.execute("INSERT INTO test VALUES (42)")
        conn.commit()
        conn.close()

        # Create snapshot
        snapshots_dir = tmp_path / "snapshots"
        result = create_timestamped_snapshot(source_db, snapshots_dir)

        assert result.snapshot_path.exists()
        assert result.source_path == source_db.resolve()
        assert (
            snapshots_dir in result.snapshot_path.parents
            or result.snapshot_path.parent == snapshots_dir
        )

    def test_snapshot_contains_data(self, tmp_path: Path):
        """Test that snapshot contains source data."""
        # Create source with data
        source_db = tmp_path / "chat.db"
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE messages (id INTEGER, text TEXT)")
        conn.execute("INSERT INTO messages VALUES (1, 'Hello')")
        conn.commit()
        conn.close()

        # Create snapshot
        snapshots_dir = tmp_path / "snapshots"
        result = create_timestamped_snapshot(source_db, snapshots_dir)

        # Verify data in snapshot
        snap_conn = sqlite3.connect(str(result.snapshot_path))
        cursor = snap_conn.execute("SELECT text FROM messages WHERE id = 1")
        row = cursor.fetchone()
        snap_conn.close()

        assert row[0] == "Hello"

    def test_custom_snapshot_name(self, tmp_path: Path):
        """Test creating snapshot with custom name."""
        source_db = tmp_path / "chat.db"
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        snapshots_dir = tmp_path / "snapshots"
        result = create_timestamped_snapshot(
            source_db, snapshots_dir, snapshot_name="custom_backup.db"
        )

        assert result.snapshot_path.name == "custom_backup.db"
        assert result.snapshot_path.exists()


class TestSnapshotInfo:
    """Tests for SnapshotInfo dataclass."""

    def test_snapshot_info_age_days(self):
        """Test age_days property calculation."""
        # Create a snapshot info from 2 days ago
        two_days_ago = datetime.now() - timedelta(days=2)
        info = SnapshotInfo(
            path=Path("/snapshots/chat_20250115_100000.db"),
            created_at=two_days_ago,
            source_stem="chat",
        )
        assert 1.9 < info.age_days < 2.1  # Allow for small timing variations


class TestParseSnapshotFilename:
    """Tests for _parse_snapshot_filename function."""

    def test_parse_valid_filename(self):
        """Parse a valid snapshot filename."""
        info = _parse_snapshot_filename("chat_20250115_103045.db")
        assert info is not None
        assert info.source_stem == "chat"
        assert info.created_at == datetime(2025, 1, 15, 10, 30, 45)

    def test_parse_invalid_filename(self):
        """Invalid filenames return None."""
        assert _parse_snapshot_filename("not_a_snapshot.db") is None
        assert _parse_snapshot_filename("chat.db") is None
        assert _parse_snapshot_filename("chat_20250115.db") is None

    def test_parse_different_stem(self):
        """Parse filename with different source stem."""
        info = _parse_snapshot_filename("mydata_20240101_000000.db")
        assert info is not None
        assert info.source_stem == "mydata"


class TestListSnapshots:
    """Tests for list_snapshots function."""

    def test_list_empty_directory(self, tmp_path: Path):
        """Empty directory returns empty list."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()
        assert list_snapshots(snapshots_dir) == []

    def test_list_nonexistent_directory(self, tmp_path: Path):
        """Nonexistent directory returns empty list."""
        snapshots_dir = tmp_path / "nonexistent"
        assert list_snapshots(snapshots_dir) == []

    def test_list_snapshots_sorted(self, tmp_path: Path):
        """Snapshots are sorted newest first."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Create snapshot files (just empty files for this test)
        (snapshots_dir / "chat_20250101_100000.db").touch()
        (snapshots_dir / "chat_20250115_100000.db").touch()
        (snapshots_dir / "chat_20250110_100000.db").touch()

        result = list_snapshots(snapshots_dir)

        assert len(result) == 3
        # Newest first
        assert result[0].path.name == "chat_20250115_100000.db"
        assert result[1].path.name == "chat_20250110_100000.db"
        assert result[2].path.name == "chat_20250101_100000.db"

    def test_list_filters_by_stem(self, tmp_path: Path):
        """List filters by source_stem."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        (snapshots_dir / "chat_20250101_100000.db").touch()
        (snapshots_dir / "other_20250115_100000.db").touch()

        result = list_snapshots(snapshots_dir, source_stem="chat")
        assert len(result) == 1
        assert result[0].source_stem == "chat"


class TestGetLatestSnapshot:
    """Tests for get_latest_snapshot function."""

    def test_get_latest_empty(self, tmp_path: Path):
        """Empty directory returns None."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()
        assert get_latest_snapshot(snapshots_dir) is None

    def test_get_latest(self, tmp_path: Path):
        """Returns the most recent snapshot."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        (snapshots_dir / "chat_20250101_100000.db").touch()
        (snapshots_dir / "chat_20250115_100000.db").touch()

        latest = get_latest_snapshot(snapshots_dir)
        assert latest is not None
        assert latest.path.name == "chat_20250115_100000.db"


class TestSnapshotNeedsRefresh:
    """Tests for snapshot_needs_refresh function."""

    def test_needs_refresh_no_snapshots(self, tmp_path: Path):
        """Returns True when no snapshots exist."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()
        assert snapshot_needs_refresh(snapshots_dir) is True

    def test_needs_refresh_old_snapshot(self, tmp_path: Path):
        """Returns True when snapshot is too old."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Create a snapshot from 10 days ago
        old_date = datetime.now() - timedelta(days=10)
        filename = f"chat_{old_date.strftime('%Y%m%d_%H%M%S')}.db"
        (snapshots_dir / filename).touch()

        assert snapshot_needs_refresh(snapshots_dir, max_age_days=7) is True

    def test_no_refresh_recent_snapshot(self, tmp_path: Path):
        """Returns False when snapshot is recent."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Create a snapshot from 1 day ago
        recent_date = datetime.now() - timedelta(days=1)
        filename = f"chat_{recent_date.strftime('%Y%m%d_%H%M%S')}.db"
        (snapshots_dir / filename).touch()

        assert snapshot_needs_refresh(snapshots_dir, max_age_days=7) is False


class TestGetOrCreateSnapshot:
    """Tests for get_or_create_snapshot function."""

    def test_creates_new_when_none_exist(self, tmp_path: Path):
        """Creates a new snapshot when none exist."""
        source_db = tmp_path / "chat.db"
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        snapshots_dir = tmp_path / "snapshots"
        result = get_or_create_snapshot(source_db, snapshots_dir)

        assert result.exists()
        assert snapshots_dir in result.parents or result.parent == snapshots_dir

    def test_reuses_recent_snapshot(self, tmp_path: Path):
        """Reuses existing snapshot if recent enough."""
        source_db = tmp_path / "chat.db"
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        snapshots_dir = tmp_path / "snapshots"

        # Create first snapshot
        first = get_or_create_snapshot(source_db, snapshots_dir)

        # Second call should return same snapshot
        second = get_or_create_snapshot(source_db, snapshots_dir)

        assert first == second

    def test_force_new_snapshot(self, tmp_path: Path):
        """force_new=True creates a new snapshot."""
        source_db = tmp_path / "chat.db"
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        snapshots_dir = tmp_path / "snapshots"

        first = get_or_create_snapshot(source_db, snapshots_dir)

        # Force new should create different snapshot
        import time

        time.sleep(1.1)  # Ensure different timestamp
        second = get_or_create_snapshot(source_db, snapshots_dir, force_new=True)

        assert first != second

    def test_raises_on_missing_source(self, tmp_path: Path):
        """Raises FileNotFoundError when source doesn't exist."""
        source_db = tmp_path / "nonexistent.db"
        snapshots_dir = tmp_path / "snapshots"

        with pytest.raises(FileNotFoundError):
            get_or_create_snapshot(source_db, snapshots_dir)


class TestCleanupOldSnapshots:
    """Tests for cleanup_old_snapshots function."""

    def test_keeps_recent_snapshots(self, tmp_path: Path):
        """Keeps the specified number of recent snapshots."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Create 5 snapshot files
        for i in range(5):
            date = datetime.now() - timedelta(days=i)
            filename = f"chat_{date.strftime('%Y%m%d_%H%M%S')}.db"
            (snapshots_dir / filename).touch()

        deleted = cleanup_old_snapshots(snapshots_dir, keep_count=3)

        assert len(deleted) == 2
        remaining = list_snapshots(snapshots_dir)
        assert len(remaining) == 3

    def test_no_deletion_when_below_threshold(self, tmp_path: Path):
        """No deletion when fewer snapshots than keep_count."""
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        (snapshots_dir / "chat_20250115_100000.db").touch()

        deleted = cleanup_old_snapshots(snapshots_dir, keep_count=3)

        assert len(deleted) == 0
