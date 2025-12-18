# Database Analysis: chat.db & Contacts Database

Comprehensive documentation of the macOS iMessage (`chat.db`) and Contacts (`AddressBook`) SQLite databases, including schema analysis, data types, file sizes, and relationships.

---

## Table of Contents

1. [Overview](#overview)
2. [chat.db (iMessage Database)](#chatdb-imessage-database)
   - [Location & Access](#location--access)
   - [Table Structure](#table-structure)
   - [Core Data Tables](#core-data-tables)
   - [Join Tables](#join-tables)
   - [Sync & Deletion Tables](#sync--deletion-tables)
   - [System Tables](#system-tables)
   - [Data Types & Formats](#data-types--formats)
   - [File Sizes & Storage](#file-sizes--storage)
   - [Indexes & Performance](#indexes--performance)
3. [Contacts Database (AddressBook)](#contacts-database-addressbook)
   - [Location & Access](#contacts-location--access)
   - [Table Structure](#contacts-table-structure)
   - [Data Types](#contacts-data-types)
4. [Database Relationships](#database-relationships)
5. [Linking Databases](#linking-databases)
6. [Query Examples](#query-examples)
7. [Analysis Opportunities](#analysis-opportunities)

---

## Overview

| Database | Purpose | Location | Typical Size |
|----------|---------|----------|--------------|
| **chat.db** | iMessage history & metadata | `~/Library/Messages/chat.db` | 100MB - 10GB+ |
| **Contacts** | Contact information | `~/Library/Application Support/AddressBook/AddressBook-v22.abcddb` | 1MB - 100MB |
| **Attachments** | Media files (photos, videos, etc.) | `~/Library/Messages/Attachments/` | 1GB - 100GB+ |

---

## chat.db (iMessage Database)

### Location & Access

| Property | Value |
|----------|-------|
| **Path** | `~/Library/Messages/chat.db` |
| **Type** | SQLite 3 |
| **Mode** | WAL (Write-Ahead Logging) |
| **Access** | Read-only recommended (`mode=ro`) |

**Related Files**:
- `chat.db-wal` — Write-Ahead Log file
- `chat.db-shm` — Shared memory file
- `~/Library/Messages/Attachments/` — Attachment files directory

**Connection Example**:
```python
import sqlite3
from pathlib import Path

db_path = Path.home() / "Library/Messages/chat.db"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

---

### Table Structure

The database contains **18 main tables** organized into 4 categories:

| Category | Tables | Count |
|----------|--------|-------|
| **Core Data** | `message`, `chat`, `handle`, `attachment` | 4 |
| **Join Tables** | `chat_message_join`, `chat_handle_join`, `message_attachment_join`, `chat_recoverable_message_join` | 4 |
| **Sync/Deletion** | `deleted_messages`, `sync_deleted_messages`, `sync_deleted_chats`, `sync_deleted_attachments` | 4 |
| **System** | `_SqliteDatabaseProperties`, `sqlite_sequence`, `sqlite_stat1`, `kvtable`, `message_processing_task`, `recoverable_message_part`, `unsynced_removed_recoverable_messages` | 6 |

---

### Core Data Tables

#### `message` — Individual Messages

**Purpose**: Stores all message content, metadata, and status information.

**Row Count**: Typically 10,000 - 1,000,000+ rows

**Key Columns** (90+ total):

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `ROWID` | INTEGER | 8 bytes | Primary key |
| `guid` | TEXT | ~36 bytes | Unique message identifier (UUID) |
| `text` | TEXT | Variable (0 - 64KB+) | Message body content |
| `attributedBody` | BLOB | Variable (0 - 100KB+) | Rich text with formatting |
| `date` | INTEGER | 8 bytes | Timestamp (nanoseconds since 2001-01-01) |
| `date_read` | INTEGER | 8 bytes | Read timestamp |
| `date_delivered` | INTEGER | 8 bytes | Delivery timestamp |
| `handle_id` | INTEGER | 8 bytes | Foreign key to `handle` |
| `service` | TEXT | ~10 bytes | 'iMessage' or 'SMS' |
| `is_from_me` | INTEGER | 1 byte | Boolean flag (0/1) |
| `is_read` | INTEGER | 1 byte | Boolean flag (0/1) |
| `is_delivered` | INTEGER | 1 byte | Boolean flag (0/1) |
| `is_sent` | INTEGER | 1 byte | Boolean flag (0/1) |
| `is_audio_message` | INTEGER | 1 byte | Boolean flag (0/1) |
| `cache_has_attachments` | INTEGER | 1 byte | Boolean flag (0/1) |
| `reply_to_guid` | TEXT | ~36 bytes | GUID of replied message |
| `thread_originator_guid` | TEXT | ~36 bytes | Original message in thread |
| `balloon_bundle_id` | TEXT | Variable | Third-party app identifier |
| `expressive_send_style_id` | TEXT | Variable | Message effect identifier |
| `payload_data` | BLOB | Variable | Binary payload data |
| `message_summary_info` | BLOB | Variable | Summary metadata |

**Storage Estimate per Row**: ~500 bytes - 10KB (varies by message content)

---

#### `chat` — Conversation Threads

**Purpose**: Represents conversation threads (1-on-1 or group chats).

**Row Count**: Typically 100 - 10,000 rows

**Key Columns**:

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `ROWID` | INTEGER | 8 bytes | Primary key |
| `guid` | TEXT | ~50 bytes | Unique chat identifier |
| `chat_identifier` | TEXT | ~30 bytes | Phone/email identifier |
| `display_name` | TEXT | Variable (0 - 100 bytes) | Contact name (shown in UI) |
| `service_name` | TEXT | ~10 bytes | Service type |
| `room_name` | TEXT | Variable | Group chat room name |
| `is_archived` | INTEGER | 1 byte | Boolean flag |
| `is_filtered` | INTEGER | 1 byte | Boolean flag |
| `properties` | BLOB | Variable (0 - 10KB) | Binary properties data |
| `last_read_message_timestamp` | INTEGER | 8 bytes | Last read timestamp |
| `syndication_date` | INTEGER | 8 bytes | Syndication timestamp |

**Storage Estimate per Row**: ~200 - 500 bytes

---

#### `handle` — Contacts/Phone Numbers

**Purpose**: Stores contact identifiers (phone numbers, email addresses).

**Row Count**: Typically 100 - 5,000 rows

**Columns**:

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `ROWID` | INTEGER | 8 bytes | Primary key |
| `id` | TEXT | ~20 bytes | Phone number or email |
| `country` | TEXT | 2 bytes | Country code (e.g., "US") |
| `service` | TEXT | ~10 bytes | Service type |
| `uncanonicalized_id` | TEXT | ~20 bytes | Original unformatted ID |
| `person_centric_id` | TEXT | ~40 bytes | Link to Contacts app |

**Storage Estimate per Row**: ~100 - 150 bytes

---

#### `attachment` — Media Files

**Purpose**: Stores metadata about attached files (photos, videos, documents).

**Row Count**: Typically 1,000 - 100,000+ rows

**Key Columns**:

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `ROWID` | INTEGER | 8 bytes | Primary key |
| `guid` | TEXT | ~36 bytes | Unique attachment identifier |
| `filename` | TEXT | Variable (50 - 200 bytes) | Full file path |
| `mime_type` | TEXT | ~20 bytes | MIME type |
| `uti` | TEXT | ~30 bytes | Uniform Type Identifier |
| `total_bytes` | INTEGER | 8 bytes | File size in bytes |
| `created_date` | INTEGER | 8 bytes | Creation timestamp |
| `is_outgoing` | INTEGER | 1 byte | Boolean flag |
| `is_sticker` | INTEGER | 1 byte | Boolean flag |
| `transfer_state` | INTEGER | 4 bytes | Transfer status code |
| `user_info` | BLOB | Variable | User metadata |
| `attribution_info` | BLOB | Variable | Attribution data |

**Storage Estimate per Row**: ~200 - 400 bytes (metadata only, not file content)

---

### Join Tables

#### `chat_message_join`

**Purpose**: Many-to-many relationship between chats and messages.

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `chat_id` | INTEGER | 8 bytes | FK to `chat.ROWID` |
| `message_id` | INTEGER | 8 bytes | FK to `message.ROWID` |
| `message_date` | INTEGER | 8 bytes | Cached message date |

**Row Count**: Equal to `message` count (typically 1:1)

---

#### `chat_handle_join`

**Purpose**: Links contacts to chats (especially for group chats).

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `chat_id` | INTEGER | 8 bytes | FK to `chat.ROWID` |
| `handle_id` | INTEGER | 8 bytes | FK to `handle.ROWID` |

**Row Count**: Sum of participants across all chats

---

#### `message_attachment_join`

**Purpose**: Links messages to their attachments.

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `message_id` | INTEGER | 8 bytes | FK to `message.ROWID` |
| `attachment_id` | INTEGER | 8 bytes | FK to `attachment.ROWID` |

**Row Count**: Equal to `attachment` count (typically 1:1)

---

#### `chat_recoverable_message_join`

**Purpose**: Tracks messages that can be recovered after deletion.

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `chat_id` | INTEGER | 8 bytes | FK to `chat.ROWID` |
| `message_id` | INTEGER | 8 bytes | FK to `message.ROWID` |
| `delete_date` | INTEGER | 8 bytes | Deletion timestamp |
| `ck_sync_state` | INTEGER | 4 bytes | CloudKit sync state |

---

### Sync & Deletion Tables

#### `deleted_messages`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `guid` | TEXT | Deleted message GUID |

#### `sync_deleted_messages`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `guid` | TEXT | Message GUID |
| `recordID` | TEXT | CloudKit record ID |

#### `sync_deleted_chats`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `guid` | TEXT | Chat GUID |
| `recordID` | TEXT | CloudKit record ID |
| `timestamp` | INTEGER | Deletion timestamp |

#### `sync_deleted_attachments`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `guid` | TEXT | Attachment GUID |
| `recordID` | TEXT | CloudKit record ID |

---

### System Tables

#### `_SqliteDatabaseProperties`

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT | Property name |
| `value` | TEXT | Property value |

#### `kvtable`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `key` | TEXT | Unique key |
| `value` | BLOB | Binary value |

**Known Keys**:
- `lastFailedMessageDate` — Timestamp of last failed message
- `lastFailedMessageRowID` — ROWID of last failed message

#### `message_processing_task`

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `guid` | TEXT | Message GUID |
| `task_flags` | INTEGER | Task type flags |

#### `recoverable_message_part`

| Column | Type | Description |
|--------|------|-------------|
| `chat_id` | INTEGER | FK to `chat.ROWID` |
| `message_id` | INTEGER | FK to `message.ROWID` |
| `part_index` | INTEGER | Part number |
| `delete_date` | INTEGER | Deletion timestamp |
| `part_text` | BLOB | Recoverable text content |
| `ck_sync_state` | INTEGER | CloudKit sync state |

---

### Data Types & Formats

#### Timestamps

**Format**: Nanoseconds since **2001-01-01 00:00:00 UTC** (Apple Cocoa epoch)

**Size**: 8 bytes (INTEGER)

**Conversion to Unix Epoch**:
```sql
datetime(
    date / 1000000000 + strftime("%s", "2001-01-01"),
    "unixepoch",
    "localtime"
) AS readable_date
```

**Python Conversion**:
```python
from datetime import datetime, timedelta

APPLE_EPOCH = datetime(2001, 1, 1)

def apple_timestamp_to_datetime(ns: int) -> datetime:
    """Convert Apple nanosecond timestamp to Python datetime."""
    return APPLE_EPOCH + timedelta(seconds=ns / 1_000_000_000)
```

---

#### Boolean Flags

**Format**: INTEGER (0 or 1)

**Size**: 1 byte (stored as INTEGER, but logically boolean)

**Common Flags**:
| Flag | Description |
|------|-------------|
| `is_from_me` | Message sent by user |
| `is_read` | Message has been read |
| `is_delivered` | Message was delivered |
| `is_sent` | Message was sent |
| `is_audio_message` | Audio message |
| `is_sticker` | Sticker attachment |
| `is_archived` | Chat is archived |
| `is_spam` | Marked as spam |

---

#### GUIDs

**Format**: UUID-like string (e.g., `p:0/E2F7A8B9-1234-5678-90AB-CDEF01234567`)

**Size**: ~36-50 bytes (TEXT)

**Usage**: Unique identifiers for CloudKit sync and message tracking

---

#### BLOBs (Binary Large Objects)

| Field | Typical Size | Contents |
|-------|--------------|----------|
| `attributedBody` | 100 bytes - 100KB | Rich text with formatting (NSAttributedString) |
| `payload_data` | Variable | App-specific payload |
| `properties` | 0 - 10KB | Chat properties (plist) |
| `message_summary_info` | Variable | Message metadata |

---

### File Sizes & Storage

#### Database File Sizes

| File | Typical Size Range | Description |
|------|-------------------|-------------|
| `chat.db` | 50MB - 5GB | Main database |
| `chat.db-wal` | 0 - 100MB | Write-ahead log |
| `chat.db-shm` | 32KB | Shared memory |

#### Attachment File Types & Sizes

| MIME Type | UTI | Typical Size | Description |
|-----------|-----|--------------|-------------|
| `image/jpeg` | `public.jpeg` | 100KB - 5MB | Photos |
| `image/png` | `public.png` | 50KB - 2MB | Screenshots, images |
| `image/heic` | `public.heic` | 500KB - 3MB | iOS photos (HEIF) |
| `image/gif` | `com.compuserve.gif` | 100KB - 10MB | Animated GIFs |
| `video/quicktime` | `com.apple.quicktime-movie` | 1MB - 500MB | Videos |
| `video/mp4` | `public.mpeg-4` | 1MB - 200MB | MP4 videos |
| `audio/amr` | `org.3gpp.adaptive-multi-rate-audio` | 10KB - 500KB | Voice messages |
| `audio/mpeg` | `public.mp3` | 1MB - 10MB | Audio files |
| `application/pdf` | `com.adobe.pdf` | 100KB - 50MB | PDF documents |
| `text/vcard` | `public.vcard` | 1KB - 10KB | Contact cards |

#### Query: Attachment Size Analysis

```sql
-- Total storage by MIME type
SELECT 
    mime_type,
    COUNT(*) AS count,
    SUM(total_bytes) AS total_bytes,
    ROUND(SUM(total_bytes) / 1024.0 / 1024.0, 2) AS total_mb,
    ROUND(AVG(total_bytes) / 1024.0, 2) AS avg_kb
FROM attachment
WHERE total_bytes > 0
GROUP BY mime_type
ORDER BY total_bytes DESC;
```

```sql
-- Storage by contact
SELECT 
    chat.display_name,
    COUNT(DISTINCT attachment.ROWID) AS attachment_count,
    SUM(attachment.total_bytes) AS total_bytes,
    ROUND(SUM(attachment.total_bytes) / 1024.0 / 1024.0, 2) AS total_mb
FROM chat
JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
JOIN message ON chat_message_join.message_id = message.ROWID
JOIN message_attachment_join ON message.ROWID = message_attachment_join.message_id
JOIN attachment ON message_attachment_join.attachment_id = attachment.ROWID
GROUP BY chat.ROWID, chat.display_name
ORDER BY total_bytes DESC
LIMIT 20;
```

#### Attachment Directory Structure

```
~/Library/Messages/Attachments/
├── 00/
│   ├── 00/
│   │   └── {GUID}/
│   │       └── filename.jpg
│   ├── 01/
│   └── ...
├── 01/
└── ...
```

**Path Pattern**: `{2-digit-hash}/{2-digit-hash}/{GUID}/{filename}`

---

### Indexes & Performance

The database includes **30+ indexes** for query optimization:

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `message_idx_date` | message | date | Date range queries |
| `message_idx_handle` | message | handle_id | Contact queries |
| `message_idx_is_read` | message | is_read | Unread filter |
| `chat_idx_chat_identifier` | chat | chat_identifier | Chat lookup |
| `chat_message_join_idx_message_date_id_chat_id` | chat_message_join | message_date, message_id, chat_id | Sorted message retrieval |

**Performance Tips**:
- Always filter by indexed columns first (`date`, `handle_id`, `chat_identifier`)
- Use `LIMIT` for large result sets
- Prefer joins over subqueries

---

## Contacts Database (AddressBook)

### Contacts Location & Access

| Property | Value |
|----------|-------|
| **Path** | `~/Library/Application Support/AddressBook/AddressBook-v22.abcddb` |
| **Type** | SQLite 3 (Core Data format) |
| **Note** | Version number (v22) varies by macOS version |

**Find Database Version**:
```python
from pathlib import Path

for db in Path.home().glob("Library/Application Support/AddressBook/AddressBook-*.abcddb"):
    print(f"Found: {db}")
```

---

### Contacts Table Structure

Core Data uses `Z` prefix convention for tables and columns.

#### `ZABCDRECORD` — Contact Records

| Column | Type | Size | Description |
|--------|------|------|-------------|
| `Z_PK` | INTEGER | 8 bytes | Primary key |
| `ZFIRSTNAME` | TEXT | Variable | First name |
| `ZLASTNAME` | TEXT | Variable | Last name |
| `ZMIDDLENAME` | TEXT | Variable | Middle name |
| `ZNICKNAME` | TEXT | Variable | Nickname |
| `ZORGANIZATION` | TEXT | Variable | Company name |
| `ZJOBTITLE` | TEXT | Variable | Job title |
| `ZDEPARTMENT` | TEXT | Variable | Department |
| `ZBIRTHDAY` | REAL | 8 bytes | Birthday (Core Data timestamp) |
| `ZNOTE` | TEXT | Variable | Notes |
| `ZPHOTO` | BLOB | Variable (0 - 1MB) | Profile photo |
| `ZTHUMBNAILIMAGE` | BLOB | Variable (0 - 50KB) | Thumbnail image |

---

#### `ZABCDPHONENUMBER` — Phone Numbers

| Column | Type | Description |
|--------|------|-------------|
| `Z_PK` | INTEGER | Primary key |
| `ZOWNER` | INTEGER | FK to `ZABCDRECORD.Z_PK` |
| `ZFULLNUMBER` | TEXT | Full phone number |
| `ZLABEL` | TEXT | Label (home, work, mobile, etc.) |
| `ZORDERINGINDEX` | INTEGER | Display order |

---

#### `ZABCDEMAILADDRESS` — Email Addresses

| Column | Type | Description |
|--------|------|-------------|
| `Z_PK` | INTEGER | Primary key |
| `ZOWNER` | INTEGER | FK to `ZABCDRECORD.Z_PK` |
| `ZADDRESS` | TEXT | Email address |
| `ZLABEL` | TEXT | Label (home, work, etc.) |

---

#### `ZABCDPOSTALADDRESS` — Physical Addresses

| Column | Type | Description |
|--------|------|-------------|
| `Z_PK` | INTEGER | Primary key |
| `ZOWNER` | INTEGER | FK to `ZABCDRECORD.Z_PK` |
| `ZSTREET` | TEXT | Street address |
| `ZCITY` | TEXT | City |
| `ZSTATE` | TEXT | State/Province |
| `ZZIPCODE` | TEXT | Postal code |
| `ZCOUNTRY` | TEXT | Country |
| `ZLABEL` | TEXT | Label (home, work, etc.) |

---

### Contacts Data Types

#### Core Data Timestamps

**Format**: Seconds since **2001-01-01 00:00:00 UTC** (as REAL/float)

**Conversion**:
```python
from datetime import datetime, timedelta

APPLE_EPOCH = datetime(2001, 1, 1)

def coredata_timestamp_to_datetime(seconds: float) -> datetime:
    return APPLE_EPOCH + timedelta(seconds=seconds)
```

#### Photo Storage

| Field | Format | Typical Size |
|-------|--------|--------------|
| `ZPHOTO` | JPEG/PNG BLOB | 50KB - 1MB |
| `ZTHUMBNAILIMAGE` | JPEG BLOB | 5KB - 50KB |

---

## Database Relationships

### chat.db Entity Relationship

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐
│    chat     │────<│  chat_message_join   │>────│   message   │
│  (thread)   │     │                      │     │  (content)  │
└─────────────┘     └──────────────────────┘     └─────────────┘
       │                                                │
       │            ┌──────────────────────┐            │
       └───────────<│   chat_handle_join   │            │
                    └──────────────────────┘            │
                              │                         │
                              ▼                         │
                    ┌─────────────────┐                 │
                    │     handle      │<────────────────┘
                    │ (phone/email)   │
                    └─────────────────┘
                              │
                              │ person_centric_id
                              ▼
                    ┌─────────────────┐
                    │  ZABCDRECORD    │  (Contacts DB)
                    │   (contact)     │
                    └─────────────────┘

┌─────────────┐     ┌──────────────────────┐     ┌─────────────┐
│   message   │────<│ message_attachment_  │>────│ attachment  │
│             │     │       join           │     │   (media)   │
└─────────────┘     └──────────────────────┘     └─────────────┘
```

### Foreign Key Summary

| Table | Column | References |
|-------|--------|------------|
| `chat_message_join` | `chat_id` | `chat.ROWID` |
| `chat_message_join` | `message_id` | `message.ROWID` |
| `chat_handle_join` | `chat_id` | `chat.ROWID` |
| `chat_handle_join` | `handle_id` | `handle.ROWID` |
| `message_attachment_join` | `message_id` | `message.ROWID` |
| `message_attachment_join` | `attachment_id` | `attachment.ROWID` |
| `message` | `handle_id` | `handle.ROWID` |
| `message` | `other_handle` | `handle.ROWID` |

---

## Linking Databases

### Method 1: Via `person_centric_id`

```python
# chat.db: handle.person_centric_id → Contacts DB
# Note: person_centric_id format may vary
```

### Method 2: Via Phone/Email Matching

```python
import sqlite3
from pathlib import Path

# Connect to both databases
chat_db = sqlite3.connect(f"file:{Path.home()/'Library/Messages/chat.db'}?mode=ro", uri=True)
contacts_db = sqlite3.connect(f"file:{Path.home()/'Library/Application Support/AddressBook/AddressBook-v22.abcddb'}?mode=ro", uri=True)

# Get handles from chat.db
handles = chat_db.execute("SELECT ROWID, id FROM handle").fetchall()

# Match to contacts
for handle_rowid, handle_id in handles:
    # Try phone number match
    contact = contacts_db.execute("""
        SELECT r.ZFIRSTNAME, r.ZLASTNAME
        FROM ZABCDRECORD r
        JOIN ZABCDPHONENUMBER p ON r.Z_PK = p.ZOWNER
        WHERE p.ZFULLNUMBER LIKE ?
    """, (f"%{handle_id[-10:]}%",)).fetchone()  # Match last 10 digits
    
    if not contact:
        # Try email match
        contact = contacts_db.execute("""
            SELECT r.ZFIRSTNAME, r.ZLASTNAME
            FROM ZABCDRECORD r
            JOIN ZABCDEMAILADDRESS e ON r.Z_PK = e.ZOWNER
            WHERE e.ZADDRESS = ?
        """, (handle_id,)).fetchone()
    
    if contact:
        print(f"{handle_id} → {contact[0]} {contact[1]}")
```

---

## Query Examples

### Messages with Full Context

```sql
SELECT
    datetime(m.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS date,
    c.display_name,
    h.id AS phone_email,
    m.text,
    m.is_from_me,
    m.service
FROM message m
JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
JOIN chat c ON cmj.chat_id = c.ROWID
LEFT JOIN handle h ON m.handle_id = h.ROWID
ORDER BY m.date DESC
LIMIT 100;
```

### Top Contacts by Message Count

```sql
SELECT
    c.display_name,
    c.chat_identifier,
    COUNT(*) AS message_count,
    SUM(CASE WHEN m.is_from_me = 1 THEN 1 ELSE 0 END) AS sent,
    SUM(CASE WHEN m.is_from_me = 0 THEN 1 ELSE 0 END) AS received
FROM chat c
JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
JOIN message m ON cmj.message_id = m.ROWID
GROUP BY c.ROWID
ORDER BY message_count DESC
LIMIT 20;
```

### Attachment Statistics by Type

```sql
SELECT 
    COALESCE(mime_type, 'unknown') AS type,
    uti,
    COUNT(*) AS count,
    ROUND(SUM(total_bytes) / 1024.0 / 1024.0, 2) AS total_mb,
    ROUND(AVG(total_bytes) / 1024.0, 2) AS avg_kb,
    ROUND(MAX(total_bytes) / 1024.0 / 1024.0, 2) AS max_mb
FROM attachment
WHERE total_bytes > 0
GROUP BY mime_type, uti
ORDER BY total_mb DESC;
```

### Database Size Summary

```sql
-- Row counts per table
SELECT 'message' AS table_name, COUNT(*) AS row_count FROM message
UNION ALL
SELECT 'chat', COUNT(*) FROM chat
UNION ALL
SELECT 'handle', COUNT(*) FROM handle
UNION ALL
SELECT 'attachment', COUNT(*) FROM attachment
UNION ALL
SELECT 'chat_message_join', COUNT(*) FROM chat_message_join
UNION ALL
SELECT 'chat_handle_join', COUNT(*) FROM chat_handle_join
UNION ALL
SELECT 'message_attachment_join', COUNT(*) FROM message_attachment_join;
```

---

## Analysis Opportunities

### By Database

| Database | Analysis Type | Data Source |
|----------|--------------|-------------|
| **chat.db** | Message frequency over time | `message.date` |
| **chat.db** | Reply time analysis | `message.date_read - message.date` |
| **chat.db** | Service usage (iMessage vs SMS) | `message.service` |
| **chat.db** | Attachment type distribution | `attachment.mime_type` |
| **chat.db** | Storage usage per contact | `attachment.total_bytes` |
| **chat.db** | Group chat dynamics | `chat_handle_join` |
| **Contacts** | Geographic distribution | `ZABCDPOSTALADDRESS` |
| **Contacts** | Contact enrichment | Name, photo, organization |
| **Combined** | Full contact analysis | Linked via phone/email |

### File Type Analysis Opportunities

| Analysis | Query Focus |
|----------|-------------|
| Storage hogs | Top 10 contacts by `total_bytes` |
| Media preferences | Distribution of `mime_type` |
| Photo vs video ratio | Filter by `image/*` vs `video/*` |
| Sticker usage | `is_sticker = 1` |
| Voice message patterns | `mime_type = 'audio/amr'` |
| Document sharing | `mime_type LIKE 'application/%'` |

---

## Security & Privacy

1. **Read-Only Access**: Always use `mode=ro` when opening databases
2. **Sensitive Data**: Both databases contain personal information
3. **Local Only**: Keep analysis local, avoid cloud uploads
4. **Anonymization**: Consider anonymizing data for exports/sharing
5. **Permissions**: macOS requires Full Disk Access for programmatic access

---

## References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [iMessage Database Analysis](https://stmorse.github.io/journal/iMessage.html)
- [Mac Address Book Schema](https://michaelwornow.net/2024/12/24/mac-address-book-schema)
- [Apple Core Data Timestamps](https://developer.apple.com/documentation/foundation/nsdate)

---

*Last Updated: 2024-12-17*
*Schema Version: macOS Sequoia / iOS 18*
