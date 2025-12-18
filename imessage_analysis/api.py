"""
FastAPI backend for iMessage Analysis.

IMPORTANT: This API ONLY reads from analysis.db (our derived database).
It NEVER accesses chat.db or AddressBook directly.

Run ./run_etl.sh first to populate analysis.db from your Apple databases.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


def _get_analysis_db_path() -> Path:
    """Get the path to analysis.db."""
    return Path(os.getenv(
        "IMESSAGE_ANALYSIS_DB_PATH",
        str(Path.home() / ".imessage_analysis" / "analysis.db")
    ))


def _open_analysis_db() -> sqlite3.Connection:
    """
    Open analysis.db for reading.
    
    Raises HTTPException if analysis.db doesn't exist.
    """
    path = _get_analysis_db_path()
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "analysis.db not found",
                "message": "Run ./run_etl.sh first to populate the analysis database",
                "path": str(path),
            }
        )
    return sqlite3.connect(str(path))


app = FastAPI(
    title="iMessage Analysis API",
    version="0.2.0",
    description="Read-only API for analysis.db. Never accesses Apple databases directly.",
)

# Local dev CORS defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("IMESSAGE_ALLOWED_ORIGIN", "http://127.0.0.1:5173"),
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check - also verifies analysis.db is accessible."""
    path = _get_analysis_db_path()
    return {
        "status": "ok" if path.exists() else "degraded",
        "analysis_db_exists": path.exists(),
        "analysis_db_path": str(path),
    }


@app.get("/summary")
def summary() -> Dict[str, Any]:
    """Get summary statistics from analysis.db."""
    conn = _open_analysis_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM fact_message")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT chat_id) FROM fact_message")
        total_chats = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_handle")
        total_handles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_person")
        total_persons = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_person WHERE source = 'contacts'")
        contacts_synced = cursor.fetchone()[0]
        
        return {
            "total_messages": total_messages,
            "total_chats": total_chats,
            "total_handles": total_handles,
            "total_persons": total_persons,
            "contacts_synced": contacts_synced,
            "table_count": 5,
            "db_path": str(_get_analysis_db_path()),
            "use_memory": False,
            "analysis_db_exists": True,
        }
    finally:
        conn.close()


@app.get("/latest")
def latest(limit: int = Query(default=25, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Get the latest messages from analysis.db."""
    conn = _open_analysis_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.date_utc,
                m.text,
                m.is_from_me,
                m.chat_id,
                h.value_raw as handle_id,
                p.display_name,
                p.first_name,
                p.last_name
            FROM fact_message m
            LEFT JOIN dim_handle h ON m.handle_id = h.handle_id
            LEFT JOIN dim_person p ON h.person_id = p.person_id
            ORDER BY m.date_utc DESC
            LIMIT ?
        """, (limit,))
        
        messages = []
        for row in cursor.fetchall():
            # Build display name
            display_name = row[5]
            if not display_name:
                if row[6] and row[7]:
                    display_name = f"{row[6]} {row[7]}"
                elif row[6]:
                    display_name = row[6]
                elif row[7]:
                    display_name = row[7]
            
            messages.append({
                "date": row[0],
                "text": row[1],
                "is_from_me": bool(row[2]),
                "chat_identifier": str(row[3]) if row[3] else None,
                "handle_id": row[4],
                "display_name": display_name,
            })
        
        return messages
    finally:
        conn.close()


@app.get("/top-chats")
def top_chats(limit: int = Query(default=50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Get top chats by message count."""
    conn = _open_analysis_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                chat_id,
                COUNT(*) as message_count
            FROM fact_message
            GROUP BY chat_id
            ORDER BY message_count DESC
            LIMIT ?
        """, (limit,))
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                "chat_identifier": str(row[0]),
                "display_name": None,
                "message_count": row[1],
            })
        
        return chats
    finally:
        conn.close()


@app.get("/contacts")
def contacts() -> List[Dict[str, Any]]:
    """
    Get all contacts sorted by most recent communication.
    """
    conn = _open_analysis_db()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                h.handle_id,
                h.value_raw,
                h.value_normalized,
                h.handle_type,
                p.person_id,
                p.first_name,
                p.last_name,
                p.display_name,
                p.source as person_source,
                COUNT(m.message_id) as message_count,
                SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) as sent_count,
                SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) as received_count,
                MIN(m.date_utc) as first_message,
                MAX(m.date_utc) as last_message
            FROM dim_handle h
            LEFT JOIN dim_person p ON h.person_id = p.person_id
            LEFT JOIN fact_message m ON m.handle_id = h.handle_id
            GROUP BY h.handle_id
            ORDER BY last_message DESC NULLS LAST, message_count DESC
        """)
        
        rows = cursor.fetchall()
        
        contacts_list = []
        for row in rows:
            # Build display name
            display_name = row[7]  # person display_name
            if not display_name:
                if row[5] and row[6]:  # first_name and last_name
                    display_name = f"{row[5]} {row[6]}"
                elif row[5]:
                    display_name = row[5]
                elif row[6]:
                    display_name = row[6]
            
            contacts_list.append({
                "handle_id": row[0],
                "id": row[1],  # value_raw (phone/email)
                "value_normalized": row[2],
                "handle_type": row[3],
                "person_id": row[4],
                "first_name": row[5],
                "last_name": row[6],
                "display_name": display_name,
                "person_source": row[8],
                "message_count": row[9] or 0,
                "sent_count": row[10] or 0,
                "received_count": row[11] or 0,
                "first_message": row[12],
                "last_message": row[13],
                # Compatibility fields
                "rowid": row[0],
                "service": "iMessage" if row[3] == "phone" else "Email" if row[3] == "email" else "Unknown",
                "country": None,
                "uncanonicalized_id": None,
                "person_centric_id": row[4],
            })
        
        return contacts_list
    finally:
        conn.close()


@app.get("/contacts/{handle_id:path}")
def contact_detail(handle_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific contact."""
    conn = _open_analysis_db()
    try:
        cursor = conn.cursor()
        
        # Find the handle
        cursor.execute("""
            SELECT 
                h.handle_id,
                h.value_raw,
                h.value_normalized,
                h.handle_type,
                p.person_id,
                p.first_name,
                p.last_name,
                p.display_name,
                p.source as person_source
            FROM dim_handle h
            LEFT JOIN dim_person p ON h.person_id = p.person_id
            WHERE h.value_raw = ? OR h.value_normalized = ?
        """, (handle_id, handle_id))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Contact not found: {handle_id}")
        
        # Build display name
        display_name = row[7]
        if not display_name:
            if row[5] and row[6]:
                display_name = f"{row[5]} {row[6]}"
            elif row[5]:
                display_name = row[5]
            elif row[6]:
                display_name = row[6]
        
        # Get message stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as from_me,
                SUM(CASE WHEN is_from_me = 0 THEN 1 ELSE 0 END) as from_them,
                SUM(CASE WHEN is_from_me = 1 THEN LENGTH(COALESCE(text, '')) ELSE 0 END) as chars_from_me,
                SUM(CASE WHEN is_from_me = 0 THEN LENGTH(COALESCE(text, '')) ELSE 0 END) as chars_from_them,
                MIN(date_utc) as first_message,
                MAX(date_utc) as last_message
            FROM fact_message
            WHERE handle_id = ?
        """, (row[0],))
        
        stats_row = cursor.fetchone()
        
        total_messages = stats_row[0] or 0
        from_me_count = stats_row[1] or 0
        from_them_count = stats_row[2] or 0
        
        return {
            "contact": {
                "handle_id": row[0],
                "id": row[1],
                "value_normalized": row[2],
                "handle_type": row[3],
                "person_id": row[4],
                "first_name": row[5],
                "last_name": row[6],
                "display_name": display_name,
                "person_source": row[8],
                "rowid": row[0],
                "service": "iMessage" if row[3] == "phone" else "Email" if row[3] == "email" else "Unknown",
                "country": None,
                "uncanonicalized_id": None,
                "person_centric_id": row[4],
            },
            "statistics": {
                "handle_id": row[1],
                "total_messages": total_messages,
                "total_characters": (stats_row[3] or 0) + (stats_row[4] or 0),
                "from_me": {
                    "message_count": from_me_count,
                    "character_count": stats_row[3] or 0,
                    "first_message": stats_row[5] if from_me_count > 0 else None,
                    "last_message": stats_row[6] if from_me_count > 0 else None,
                    "percentage": (from_me_count / total_messages * 100) if total_messages > 0 else 0,
                },
                "from_them": {
                    "message_count": from_them_count,
                    "character_count": stats_row[4] or 0,
                    "first_message": stats_row[5] if from_them_count > 0 else None,
                    "last_message": stats_row[6] if from_them_count > 0 else None,
                    "percentage": (from_them_count / total_messages * 100) if total_messages > 0 else 0,
                },
            },
            "chats": [],
        }
    finally:
        conn.close()


@app.get("/diagnostics")
def diagnostics() -> Dict[str, Any]:
    """
    Get diagnostic information about the analysis database.
    
    Shows stats on contact enrichment, data quality, etc.
    """
    path = _get_analysis_db_path()
    
    if not path.exists():
        return {
            "status": "not_initialized",
            "analysis_db_exists": False,
            "analysis_db_path": str(path),
            "message": "Run ./run_etl.sh to initialize analysis.db",
        }
    
    conn = sqlite3.connect(str(path))
    try:
        cursor = conn.cursor()
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM dim_handle")
        total_handles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_person")
        total_persons = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fact_message")
        total_messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_contact_method")
        total_contact_methods = cursor.fetchone()[0]
        
        # Person source breakdown
        cursor.execute("""
            SELECT source, COUNT(*) 
            FROM dim_person 
            GROUP BY source
        """)
        person_sources = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Handles with names
        cursor.execute("""
            SELECT COUNT(*) FROM dim_handle h
            JOIN dim_person p ON h.person_id = p.person_id
            WHERE p.display_name IS NOT NULL 
               OR p.first_name IS NOT NULL 
               OR p.last_name IS NOT NULL
        """)
        handles_with_names = cursor.fetchone()[0]
        
        # Handles linked to contacts (not inferred)
        cursor.execute("""
            SELECT COUNT(*) FROM dim_handle h
            JOIN dim_person p ON h.person_id = p.person_id
            WHERE p.source = 'contacts'
        """)
        handles_from_contacts = cursor.fetchone()[0]
        
        # Handles with no person
        cursor.execute("SELECT COUNT(*) FROM dim_handle WHERE person_id IS NULL")
        handles_unlinked = cursor.fetchone()[0]
        
        # Handle types
        cursor.execute("""
            SELECT handle_type, COUNT(*) 
            FROM dim_handle 
            GROUP BY handle_type
        """)
        handle_types = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Messages date range
        cursor.execute("SELECT MIN(date_utc), MAX(date_utc) FROM fact_message")
        date_row = cursor.fetchone()
        
        # ETL state
        cursor.execute("SELECT key, value FROM etl_state")
        etl_state = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Top contacts by message count (for sampling)
        cursor.execute("""
            SELECT 
                h.value_raw,
                p.display_name,
                p.first_name,
                p.last_name,
                p.source,
                COUNT(m.message_id) as msg_count
            FROM dim_handle h
            LEFT JOIN dim_person p ON h.person_id = p.person_id
            LEFT JOIN fact_message m ON m.handle_id = h.handle_id
            GROUP BY h.handle_id
            ORDER BY msg_count DESC
            LIMIT 10
        """)
        top_contacts = []
        for row in cursor.fetchall():
            name = row[1] or (f"{row[2]} {row[3]}" if row[2] and row[3] else row[2] or row[3])
            top_contacts.append({
                "id": row[0],
                "display_name": name,
                "source": row[4],
                "message_count": row[5],
                "has_name": name is not None,
            })
        
        return {
            "status": "ok",
            "analysis_db_exists": True,
            "analysis_db_path": str(path),
            
            "counts": {
                "handles": total_handles,
                "persons": total_persons,
                "messages": total_messages,
                "contact_methods": total_contact_methods,
            },
            
            "enrichment": {
                "handles_total": total_handles,
                "handles_with_names": handles_with_names,
                "handles_from_contacts": handles_from_contacts,
                "handles_unlinked": handles_unlinked,
                "name_coverage_percent": round(handles_with_names / total_handles * 100, 1) if total_handles > 0 else 0,
                "contacts_coverage_percent": round(handles_from_contacts / total_handles * 100, 1) if total_handles > 0 else 0,
            },
            
            "person_sources": person_sources,
            "handle_types": handle_types,
            
            "date_range": {
                "first_message": date_row[0] if date_row else None,
                "last_message": date_row[1] if date_row else None,
            },
            
            "etl_state": etl_state,
            "top_contacts_sample": top_contacts,
            
            # Profile pictures - not yet implemented
            "profile_pictures": {
                "supported": False,
                "message": "Profile picture extraction not yet implemented",
            },
        }
    finally:
        conn.close()
