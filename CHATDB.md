# chat.db Database Schema & Analysis

Complete documentation of the iMessage `chat.db` SQLite database structure, relationships, and visualization opportunities.

## Database Location

- **Path**: `~/Library/Messages/chat.db`
- **Type**: SQLite 3 database
- **Mode**: Read-only recommended (use `mode=ro` URI parameter)
- **Related Files**:
  - `chat.db-wal` - Write-Ahead Log (WAL mode)
  - `chat.db-shm` - Shared memory file
  - `~/Library/Messages/Attachments/` - Attachment files directory

## Table Overview

The database contains **18 main tables** organized into these categories:

1. **Core Data Tables** (4): `message`, `chat`, `handle`, `attachment`
2. **Join Tables** (4): `chat_message_join`, `chat_handle_join`, `message_attachment_join`, `chat_recoverable_message_join`
3. **Sync/Deletion Tables** (4): `deleted_messages`, `sync_deleted_messages`, `sync_deleted_chats`, `sync_deleted_attachments`
4. **System Tables** (6): `_SqliteDatabaseProperties`, `sqlite_sequence`, `sqlite_stat1`, `kvtable`, `message_processing_task`, `unsynced_removed_recoverable_messages`, `recoverable_message_part`

---

## Core Data Tables

### 1. `message` - Individual Messages

**Purpose**: Stores all message content, metadata, and status information.

**Key Columns**:

| Column | Type | Description | Visualization Opportunity |
|--------|------|-------------|---------------------------|
| `ROWID` | INTEGER | Primary key | - |
| `guid` | TEXT | Unique message identifier | Track message lifecycle |
| `text` | TEXT | Message body content | Word clouds, sentiment analysis, keyword trends |
| `date` | INTEGER | Timestamp (nanoseconds since 2001-01-01) | Time series, activity patterns, reply time analysis |
| `handle_id` | INTEGER | Foreign key to `handle` | Contact-based analysis |
| `is_from_me` | INTEGER | 0/1 flag | Conversation balance, initiation patterns |
| `is_read` | INTEGER | 0/1 flag | Read receipt analysis, response patterns |
| `is_delivered` | INTEGER | 0/1 flag | Delivery success rate |
| `date_read` | INTEGER | Read timestamp | Reply time distribution |
| `date_delivered` | INTEGER | Delivery timestamp | Delivery time analysis |
| `service` | TEXT | 'iMessage' or 'SMS' | Service usage breakdown |
| `error` | INTEGER | Error code (0 = success) | Failure rate analysis |
| `is_audio_message` | INTEGER | 0/1 flag | Audio vs text ratio |
| `is_emote` | INTEGER | 0/1 flag | Reaction/emoji usage |
| `cache_has_attachments` | INTEGER | 0/1 flag | Attachment frequency |
| `reply_to_guid` | TEXT | GUID of replied message | Thread depth, conversation trees |
| `associated_message_guid` | TEXT | Related message GUID | Message relationships |
| `thread_originator_guid` | TEXT | Original message in thread | Thread analysis |
| `expire_state` | INTEGER | Expiration status | Disappearing message tracking |
| `date_edited` | INTEGER | Edit timestamp | Edit frequency |
| `date_retracted` | INTEGER | Retraction timestamp | Retraction patterns |
| `is_spam` | INTEGER | 0/1 flag | Spam detection patterns |
| `item_type` | INTEGER | Message type code | Message type distribution |
| `message_action_type` | INTEGER | Action type (e.g., group add/remove) | Group dynamics |
| `group_title` | TEXT | Group name (for group actions) | Group activity tracking |
| `balloon_bundle_id` | TEXT | App/plugin identifier | Third-party app usage |
| `expressive_send_style_id` | TEXT | Effect/style identifier | Message effect usage |
| `sort_id` | INTEGER | Display sort order | Message ordering |

**Total Columns**: ~90+ columns

**Visualization Ideas**:
- **Time Series**: Messages per day/hour/week with filters (service, contact, read status)
- **Heatmaps**: Activity by hour-of-day × day-of-week
- **Reply Time Distribution**: Histogram of time-to-reply (date_read - date)
- **Service Breakdown**: Pie chart of iMessage vs SMS usage
- **Delivery Success Rate**: Percentage of delivered vs failed messages
- **Thread Depth**: Network graph showing reply chains
- **Message Type Distribution**: Bar chart of item_type frequencies
- **Edit/Retract Timeline**: Timeline showing when messages were edited/retracted
- **Read Receipt Patterns**: Heatmap of read times vs sent times
- **Audio vs Text**: Ratio over time

---

### 2. `chat` - Conversation Threads

**Purpose**: Represents conversation threads (1-on-1 or group chats).

**Key Columns**:

| Column | Type | Description | Visualization Opportunity |
|--------|------|-------------|---------------------------|
| `ROWID` | INTEGER | Primary key | - |
| `guid` | TEXT | Unique chat identifier | - |
| `chat_identifier` | TEXT | Phone/email identifier | Contact identification |
| `display_name` | TEXT | **Contact name** (shown in Messages app) | Name-based grouping |
| `service_name` | TEXT | Service type | Service distribution |
| `room_name` | TEXT | Group chat room name | Group chat identification |
| `is_archived` | INTEGER | 0/1 flag | Archive patterns |
| `is_filtered` | INTEGER | 0/1 flag | Filtered chat tracking |
| `last_addressed_handle` | TEXT | Last contacted handle | Recent activity |
| `last_read_message_timestamp` | INTEGER | Last read timestamp | Engagement tracking |
| `group_id` | TEXT | Group identifier | Group chat analysis |
| `style` | INTEGER | Chat style code | Chat type classification |
| `state` | INTEGER | Chat state | State transitions |
| `properties` | BLOB | Binary properties | Advanced metadata |
| `ck_sync_state` | INTEGER | CloudKit sync state | Sync status |
| `syndication_date` | INTEGER | Syndication timestamp | Content sharing |
| `syndication_type` | INTEGER | Syndication type | Sharing patterns |

**Visualization Ideas**:
- **Top Chats**: Bar chart of message count per chat (with display_name)
- **Archive Patterns**: Timeline of when chats were archived
- **Group vs 1-on-1**: Distribution of chat types
- **Last Activity**: Heatmap of last_read_message_timestamp
- **Chat Duration**: Timeline showing chat start/end dates
- **Service Distribution**: Pie chart of service_name breakdown
- **Engagement Score**: Scatter plot of message count vs last_read timestamp

---

### 3. `handle` - Contacts/Phone Numbers

**Purpose**: Stores contact identifiers (phone numbers, email addresses).

**Key Columns**:

| Column | Type | Description | Visualization Opportunity |
|--------|------|-------------|---------------------------|
| `ROWID` | INTEGER | Primary key | - |
| `id` | TEXT | **Phone number or email** | Contact identification |
| `country` | TEXT | Country code | Geographic distribution |
| `service` | TEXT | Service type | Service preferences per contact |
| `uncanonicalized_id` | TEXT | Original unformatted ID | ID normalization tracking |
| `person_centric_id` | TEXT | **Apple Contacts link** | Link to Contacts app |

**Visualization Ideas**:
- **Contact Network**: Graph showing relationships between contacts
- **Country Distribution**: World map or bar chart of countries
- **Service Preferences**: Stacked bar chart of service types per contact
- **Contact Frequency**: Top contacts by message count
- **Multi-Service Contacts**: Contacts using multiple services (iMessage + SMS)

---

### 4. `attachment` - Media Files

**Purpose**: Stores metadata about attached files (photos, videos, documents).

**Key Columns**:

| Column | Type | Description | Visualization Opportunity |
|--------|------|-------------|---------------------------|
| `ROWID` | INTEGER | Primary key | - |
| `guid` | TEXT | Unique attachment identifier | - |
| `filename` | TEXT | File name | File type analysis |
| `mime_type` | TEXT | MIME type (e.g., 'image/jpeg') | Media type distribution |
| `uti` | TEXT | Uniform Type Identifier | File format breakdown |
| `total_bytes` | INTEGER | File size in bytes | Storage usage analysis |
| `created_date` | INTEGER | Creation timestamp | Attachment timeline |
| `start_date` | INTEGER | Start timestamp | Media capture time |
| `is_outgoing` | INTEGER | 0/1 flag | Send vs receive ratio |
| `is_sticker` | INTEGER | 0/1 flag | Sticker usage |
| `transfer_state` | INTEGER | Transfer status | Transfer success rate |
| `is_commsafety_sensitive` | INTEGER | 0/1 flag | Safety filtering |

**Visualization Ideas**:
- **Media Type Distribution**: Pie chart of mime_type breakdown
- **Storage Usage**: Bar chart of total_bytes per contact/chat
- **Attachment Timeline**: Time series of attachments over time
- **File Size Distribution**: Histogram of file sizes
- **Sticker Usage**: Timeline of sticker sends
- **Transfer Success Rate**: Percentage of successful transfers
- **Media by Contact**: Stacked bar chart showing attachment types per contact
- **Storage Growth**: Cumulative storage usage over time

---

## Join Tables

### 5. `chat_message_join` - Chat-Message Relationship

**Purpose**: Many-to-many relationship between chats and messages.

**Columns**:
- `chat_id` (INTEGER) - Foreign key to `chat.ROWID`
- `message_id` (INTEGER) - Foreign key to `message.ROWID`
- `message_date` (INTEGER) - Cached message date for performance

**Visualization Ideas**:
- **Messages per Chat**: Distribution of message counts
- **Chat Activity Timeline**: Messages per chat over time
- **Multi-Chat Messages**: Messages that appear in multiple chats (rare)

---

### 6. `chat_handle_join` - Chat-Contact Relationship

**Purpose**: Links contacts to chats (especially for group chats).

**Columns**:
- `chat_id` (INTEGER) - Foreign key to `chat.ROWID`
- `handle_id` (INTEGER) - Foreign key to `handle.ROWID`

**Visualization Ideas**:
- **Group Chat Size Distribution**: Histogram of participants per group chat
- **Contact Overlap**: Network graph showing contacts who appear in multiple chats together
- **Group Chat Networks**: Graph visualization of group chat relationships
- **Most Connected Contacts**: Contacts appearing in the most group chats

---

### 7. `message_attachment_join` - Message-Attachment Relationship

**Purpose**: Links messages to their attachments.

**Columns**:
- `message_id` (INTEGER) - Foreign key to `message.ROWID`
- `attachment_id` (INTEGER) - Foreign key to `attachment.ROWID`

**Visualization Ideas**:
- **Attachments per Message**: Distribution (most messages have 0, some have multiple)
- **Media-Rich Conversations**: Chats with high attachment rates
- **Attachment Patterns**: Timeline of attachment-heavy periods

---

### 8. `chat_recoverable_message_join` - Recoverable Messages

**Purpose**: Tracks messages that can be recovered after deletion.

**Columns**:
- `chat_id` (INTEGER) - Foreign key to `chat.ROWID`
- `message_id` (INTEGER) - Foreign key to `message.ROWID`
- `delete_date` (INTEGER) - When message was deleted
- `ck_sync_state` (INTEGER) - CloudKit sync state

**Visualization Ideas**:
- **Deletion Patterns**: Timeline of message deletions
- **Recovery Rate**: Percentage of messages that are recoverable
- **Deletion by Contact**: Which contacts have most deleted messages

---

## Sync & Deletion Tables

### 9. `deleted_messages` - Deleted Message Tracking

**Purpose**: Tracks permanently deleted messages.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `guid` (TEXT) - Message GUID

**Visualization Ideas**:
- **Deletion Timeline**: When messages were deleted
- **Deletion Frequency**: Rate of deletions over time

---

### 10. `sync_deleted_messages` - CloudKit Sync for Deletions

**Purpose**: Tracks deletions for CloudKit synchronization.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `guid` (TEXT) - Message GUID
- `recordID` (TEXT) - CloudKit record ID

---

### 11. `sync_deleted_chats` - CloudKit Sync for Chat Deletions

**Purpose**: Tracks chat deletions for CloudKit sync.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `guid` (TEXT) - Chat GUID
- `recordID` (TEXT) - CloudKit record ID
- `timestamp` (INTEGER) - Deletion timestamp

---

### 12. `sync_deleted_attachments` - CloudKit Sync for Attachment Deletions

**Purpose**: Tracks attachment deletions for CloudKit sync.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `guid` (TEXT) - Attachment GUID
- `recordID` (TEXT) - CloudKit record ID

---

## System Tables

### 13. `_SqliteDatabaseProperties` - Database Metadata

**Purpose**: Stores database-level properties.

**Columns**:
- `key` (TEXT) - Property name
- `value` (TEXT) - Property value

**Visualization Ideas**:
- **Database Version**: Track schema versions
- **Metadata Timeline**: Changes to database properties over time

---

### 14. `kvtable` - Key-Value Store

**Purpose**: General-purpose key-value storage for app state.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `key` (TEXT) - Unique key
- `value` (BLOB) - Binary value

**Known Keys** (from triggers):
- `lastFailedMessageDate` - Timestamp of last failed message
- `lastFailedMessageRowID` - ROWID of last failed message

**Visualization Ideas**:
- **App State Tracking**: Timeline of key-value changes
- **Failure Patterns**: Analysis of `lastFailedMessageDate`

---

### 15. `message_processing_task` - Background Tasks

**Purpose**: Tracks background message processing tasks.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `guid` (TEXT) - Message GUID
- `task_flags` (INTEGER) - Task type flags

**Visualization Ideas**:
- **Task Queue Depth**: Number of pending tasks
- **Task Processing Time**: Duration analysis

---

### 16. `recoverable_message_part` - Recoverable Message Content

**Purpose**: Stores recoverable parts of deleted messages.

**Columns**:
- `chat_id` (INTEGER) - Foreign key to `chat.ROWID`
- `message_id` (INTEGER) - Foreign key to `message.ROWID`
- `part_index` (INTEGER) - Part number
- `delete_date` (INTEGER) - Deletion timestamp
- `part_text` (BLOB) - Recoverable text content
- `ck_sync_state` (INTEGER) - CloudKit sync state

**Visualization Ideas**:
- **Recovery Success Rate**: Percentage of recoverable content
- **Recovery Timeline**: When content becomes recoverable

---

### 17. `unsynced_removed_recoverable_messages` - Unsynced Recoverable Deletions

**Purpose**: Tracks recoverable messages that haven't been synced yet.

**Columns**:
- `ROWID` (INTEGER) - Primary key
- `chat_guid` (TEXT) - Chat GUID
- `message_guid` (TEXT) - Message GUID
- `part_index` (INTEGER) - Part number

---

### 18. `sqlite_sequence` - Auto-increment Sequences

**Purpose**: SQLite internal table for auto-increment sequences.

**Columns**:
- `name` (TEXT) - Table name
- `seq` (INTEGER) - Last sequence value

---

## Data Types & Formats

### Timestamps

**Format**: Nanoseconds since **2001-01-01 00:00:00 UTC**

**Conversion**:
```sql
-- Convert to readable datetime
datetime(
    date / 1000000000 + strftime("%s", "2001-01-01"),
    "unixepoch",
    "localtime"
) AS readable_date
```

**Visualization**: All time-based visualizations need this conversion.

---

### Boolean Flags

Most boolean columns use `INTEGER` with:
- `0` = False
- `1` = True

**Common flags**:
- `is_from_me`, `is_read`, `is_delivered`, `is_sent`, `is_archived`, etc.

---

### GUIDs

**Format**: Unique identifiers (UUID-like strings)

**Usage**: Used for CloudKit sync and message tracking.

---

## Relationships & Foreign Keys

```
chat (1) ──< (many) chat_message_join (many) >── (1) message
chat (1) ──< (many) chat_handle_join (many) >── (1) handle
message (1) ──< (many) message_attachment_join (many) >── (1) attachment
message.handle_id ──> (1) handle.ROWID
message.other_handle ──> (1) handle.ROWID
```

---

## Visualization Recommendations by Category

### 1. Activity & Time Patterns

**High Priority**:
- **Messages per Day/Hour**: Time series with filters (contact, service, read status)
- **Activity Heatmap**: Hour-of-day × Day-of-week
- **Reply Time Distribution**: Histogram of response times
- **Service Usage Over Time**: iMessage vs SMS trends

**Medium Priority**:
- **Weekend vs Weekday**: Activity comparison
- **Holiday Patterns**: Activity around holidays
- **Time Zone Analysis**: Activity by time of day (if timezone data available)

---

### 2. Contact & Relationship Analysis

**High Priority**:
- **Top Contacts**: Bar chart with message counts (using `display_name`)
- **Contact Network Graph**: Visualize relationships between contacts
- **Group Chat Networks**: Graph of group chat participants
- **Contact Overlap**: Contacts who appear together in multiple chats

**Medium Priority**:
- **Country Distribution**: Geographic spread of contacts
- **Service Preferences**: iMessage vs SMS per contact
- **Contact Engagement Score**: Message count × recency

---

### 3. Message Content Analysis

**High Priority**:
- **Word Clouds**: Most common words per contact/chat
- **Keyword Trends**: Time series of specific keywords
- **Message Length Distribution**: Histogram of text lengths
- **Emoji Usage**: Most common emojis over time

**Medium Priority**:
- **Sentiment Analysis**: Positive/negative sentiment trends
- **Topic Modeling**: Identify conversation topics
- **Language Detection**: Multi-language support analysis

---

### 4. Media & Attachments

**High Priority**:
- **Media Type Distribution**: Pie chart of mime_type
- **Storage Usage**: Total bytes per contact/chat
- **Attachment Timeline**: When attachments were shared
- **Sticker Usage**: Sticker send frequency

**Medium Priority**:
- **File Size Distribution**: Histogram of attachment sizes
- **Transfer Success Rate**: Percentage of successful transfers
- **Media-Rich Conversations**: Chats with high attachment rates

---

### 5. Message Status & Delivery

**High Priority**:
- **Delivery Success Rate**: Percentage delivered vs failed
- **Read Receipt Patterns**: Read time vs send time heatmap
- **Error Analysis**: Failed message patterns
- **Service Downgrade Tracking**: iMessage → SMS downgrades

**Medium Priority**:
- **Delivery Time Distribution**: Time to delivery
- **Read Time Distribution**: Time to read
- **Retry Patterns**: Failed message retry attempts

---

### 6. Group Chat Dynamics

**High Priority**:
- **Group Size Distribution**: Participants per group chat
- **Group Activity Timeline**: Messages per group over time
- **Most Active Groups**: Top group chats by message count
- **Group Action Timeline**: Add/remove member events

**Medium Priority**:
- **Group Chat Networks**: Visualize group relationships
- **Group Engagement**: Activity levels per participant
- **Group Formation Patterns**: When groups were created

---

### 7. Advanced Features

**High Priority**:
- **Thread Depth Analysis**: Reply chain visualization
- **Edit/Retract Timeline**: When messages were edited/retracted
- **Disappearing Messages**: Expire_state tracking
- **Message Effects Usage**: expressive_send_style_id frequency

**Medium Priority**:
- **Third-Party App Usage**: balloon_bundle_id analysis
- **Reaction Patterns**: is_emote usage over time
- **Audio Message Trends**: Audio vs text ratio

---

## Contacts App Database Integration

### Location

**Path**: `~/Library/Application Support/AddressBook/AddressBook-v22.abcddb`

**Note**: Version number (v22) may vary by macOS version.

### Key Tables

1. **`ZABCDRECORD`**: Primary contact records
   - `Z_PK` - Primary key
   - `ZFIRSTNAME`, `ZLASTNAME` - Name fields
   - `ZPHOTO` - Profile photo (BLOB)

2. **`ZABCDPHONENUMBER`**: Phone numbers
   - `ZOWNER` - Foreign key to `ZABCDRECORD.Z_PK`
   - `ZFULLNUMBER` - Phone number

3. **`ZABCDEMAILADDRESS`**: Email addresses
   - `ZOWNER` - Foreign key to `ZABCDRECORD.Z_PK`
   - `ZADDRESS` - Email address

4. **`ZABCDPOSTALADDRESS`**: Physical addresses
   - `ZOWNER` - Foreign key to `ZABCDRECORD.Z_PK`

### Linking chat.db to Contacts

**Method 1**: Use `handle.person_centric_id` to link to Contacts database
**Method 2**: Match `handle.id` (phone/email) to `ZABCDPHONENUMBER.ZFULLNUMBER` or `ZABCDEMAILADDRESS.ZADDRESS`

### What You Can Get from Contacts

- **Full Name**: `ZFIRSTNAME` + `ZLASTNAME`
- **Profile Photo**: `ZPHOTO` (BLOB - can be saved as image file)
- **Email Addresses**: Multiple emails per contact
- **Phone Numbers**: Multiple phone numbers per contact
- **Physical Addresses**: Home, work, etc.
- **Notes**: Contact notes
- **Organization**: Company name
- **Birthday**: Date of birth
- **Relationships**: Family members, etc.

### Accessing Contacts Database

```python
import sqlite3
from pathlib import Path

contacts_db = Path.home() / "Library/Application Support/AddressBook/AddressBook-v22.abcddb"

# Find database version
for db_file in Path.home().glob("Library/Application Support/AddressBook/AddressBook-*.abcddb"):
    print(f"Found: {db_file}")

# Connect (read-only)
conn = sqlite3.connect(f"file:{contacts_db}?mode=ro", uri=True)

# Query contacts
cursor = conn.execute("""
    SELECT 
        r.Z_PK,
        r.ZFIRSTNAME,
        r.ZLASTNAME,
        p.ZFULLNUMBER,
        e.ZADDRESS
    FROM ZABCDRECORD r
    LEFT JOIN ZABCDPHONENUMBER p ON r.Z_PK = p.ZOWNER
    LEFT JOIN ZABCDEMAILADDRESS e ON r.Z_PK = e.ZOWNER
""")
```

### Visualization Opportunities with Contacts

- **Profile Photos**: Display contact photos in UI
- **Contact Cards**: Rich contact information display
- **Relationship Graphs**: Visualize contact relationships
- **Geographic Maps**: Plot contacts by address
- **Birthday Calendar**: Show upcoming birthdays
- **Organization Networks**: Group contacts by company

---

## Query Patterns & Examples

### Get Messages with Contact Names

```sql
SELECT
    datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS date,
    message.text,
    chat.display_name,
    handle.id AS phone_email,
    message.is_from_me
FROM message
JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
JOIN chat ON chat_message_join.chat_id = chat.ROWID
LEFT JOIN handle ON message.handle_id = handle.ROWID
ORDER BY message.date DESC
LIMIT 100;
```

### Get Top Contacts with Message Counts

```sql
SELECT
    chat.display_name,
    chat.chat_identifier,
    COUNT(*) AS message_count
FROM chat
JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
JOIN message ON chat_message_join.message_id = message.ROWID
GROUP BY chat.ROWID, chat.display_name, chat.chat_identifier
ORDER BY message_count DESC
LIMIT 20;
```

### Get Reply Times

```sql
SELECT
    chat.display_name,
    (message.date_read - message.date) / 1000000000.0 / 3600.0 AS hours_to_reply
FROM message
JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
JOIN chat ON chat_message_join.chat_id = chat.ROWID
WHERE message.is_from_me = 0
  AND message.date_read IS NOT NULL
  AND message.date_read > message.date
ORDER BY hours_to_reply;
```

### Get Attachment Statistics

```sql
SELECT
    chat.display_name,
    COUNT(DISTINCT message.ROWID) AS messages_with_attachments,
    SUM(attachment.total_bytes) AS total_bytes
FROM chat
JOIN chat_message_join ON chat.ROWID = chat_message_join.chat_id
JOIN message ON chat_message_join.message_id = message.ROWID
JOIN message_attachment_join ON message.ROWID = message_attachment_join.message_id
JOIN attachment ON message_attachment_join.attachment_id = attachment.ROWID
GROUP BY chat.ROWID, chat.display_name
ORDER BY total_bytes DESC;
```

---

## Indexes & Performance

The database includes **30+ indexes** for performance:

- **Date indexes**: `message_idx_date`, `chat_message_join_idx_message_date_id_chat_id`
- **Handle indexes**: `message_idx_handle`, `message_idx_handle_id`
- **Chat indexes**: `chat_idx_chat_identifier`, `chat_idx_chat_identifier_service_name`
- **Status indexes**: `message_idx_is_read`, `message_idx_is_sent_is_from_me_error`
- **Attachment indexes**: `message_idx_cache_has_attachments`

**Performance Tips**:
- Use indexes for date ranges: `WHERE message.date > ? AND message.date < ?`
- Join on indexed columns: `chat.chat_identifier`, `message.handle_id`
- Use `LIMIT` for large result sets
- Consider in-memory database for read-heavy analysis

---

## Triggers & Automation

The database includes **15+ triggers** that:
- Maintain referential integrity
- Update cached fields (`cache_roomnames`, `cache_has_attachments`)
- Track deletions for sync
- Clean up orphaned records

**Important**: These triggers run automatically - be aware when analyzing deletion patterns.

---

## Data Quality Notes

1. **Missing Data**: Some fields may be NULL (e.g., `display_name` for SMS-only contacts)
2. **Data Consistency**: `cache_*` fields are maintained by triggers but may lag
3. **Timestamps**: All dates are in nanoseconds since 2001-01-01
4. **GUIDs**: Unique but not necessarily sequential
5. **BLOBs**: Some fields store binary data (properties, attributedBody)

---

## Security & Privacy Considerations

1. **Read-Only Access**: Always use `mode=ro` when opening the database
2. **Sensitive Data**: Messages contain personal information
3. **Contacts Linking**: Be careful when linking to Contacts database
4. **Data Export**: Consider anonymization for exported data
5. **Local Storage**: Keep analysis local - don't upload to cloud services

---

## Future Analysis Opportunities

1. **Machine Learning**: Sentiment analysis, topic modeling, spam detection
2. **Network Analysis**: Contact relationship graphs, influence mapping
3. **Temporal Patterns**: Seasonal trends, life event detection
4. **Content Analysis**: Language detection, keyword extraction, entity recognition
5. **Predictive Analytics**: Response time prediction, conversation continuation
6. **Visualization Dashboards**: Interactive charts, filters, drill-downs

---

## References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [iMessage Database Analysis](https://stmorse.github.io/journal/iMessage.html)
- [Mac Address Book Schema](https://michaelwornow.net/2024/12/24/mac-address-book-schema)

---

*Last Updated: 2025-12-17*
*Database Schema Version: Based on macOS Messages app*
