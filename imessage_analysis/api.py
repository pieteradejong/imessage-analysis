"""
FastAPI backend for iMessage Analysis.

This is a thin HTTP layer over the existing analysis functions.
It is intended for local development and personal use.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from imessage_analysis.analysis import (
    get_database_summary,
    get_latest_messages_data,
    get_message_statistics_by_chat,
)
from imessage_analysis.config import get_config
from imessage_analysis.database import DatabaseConnection
from imessage_analysis.snapshot import create_timestamped_snapshot


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_db_path() -> Optional[str]:
    # Prefer explicit env var; otherwise fall back to package config auto-detection.
    env_path = os.getenv("IMESSAGE_DB_PATH")
    if env_path:
        return env_path
    return None


def _open_db() -> DatabaseConnection:
    config = get_config(db_path=_resolve_db_path())
    if not config.validate():
        # Raise a normal exception (FastAPI will 500). For local use this is fine;
        # we can improve to a proper HTTP error later.
        raise RuntimeError(
            "Database file not found or not readable. "
            "Set IMESSAGE_DB_PATH or place chat.db in CWD."
        )

    if _env_bool("IMESSAGE_SNAPSHOT", default=False):
        snapshot_dir = Path(os.getenv("IMESSAGE_SNAPSHOT_DIR", "snapshots"))
        result = create_timestamped_snapshot(Path(config.db_path_str), snapshot_dir)
        config = get_config(db_path=str(result.snapshot_path))

    use_memory = _env_bool("IMESSAGE_USE_MEMORY", default=False)
    db = DatabaseConnection(config, use_memory=use_memory)
    db.connect()
    return db


app = FastAPI(title="iMessage Analysis API", version="0.1.0")

# Local dev CORS defaults: allow the Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("IMESSAGE_ALLOWED_ORIGIN", "http://127.0.0.1:5173"),
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/summary")
def summary() -> Dict[str, Any]:
    db = _open_db()
    try:
        data = get_database_summary(db)
        data["db_path"] = db.config.db_path_str
        data["use_memory"] = bool(getattr(db, "use_memory", False))
        return data
    finally:
        db.close()


@app.get("/latest")
def latest(
    limit: int = Query(default=25, ge=1, le=500),
) -> List[Dict[str, Any]]:
    db = _open_db()
    try:
        return get_latest_messages_data(db, limit=limit)
    finally:
        db.close()


@app.get("/top-chats")
def top_chats(
    limit: int = Query(default=50, ge=1, le=500),
) -> List[Dict[str, Any]]:
    db = _open_db()
    try:
        stats = get_message_statistics_by_chat(db)
        return stats[:limit]
    finally:
        db.close()

