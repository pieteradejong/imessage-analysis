from datetime import datetime
from pathlib import Path

from imessage_analysis.snapshot import _default_snapshot_filename


def test_default_snapshot_filename():
    created_at = datetime(2025, 12, 17, 10, 11, 12)
    name = _default_snapshot_filename(Path("chat.db"), created_at)
    assert name == "chat_20251217_101112.db"
