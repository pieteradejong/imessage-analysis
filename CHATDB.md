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

## Location Data & Geographic Analysis

### Available Location Data Sources

The iMessage database provides several sources of location information, though none provide precise GPS coordinates directly in the database:

#### 1. Country Codes (Phone Number Based)

**Source**: `handle.country` and `message.country` fields

**What it contains**:
- Country code derived from phone number formatting
- Example values: "US", "CA", "GB", "FR", etc.
- May be NULL for email-based contacts

**Limitations**:
- Only country-level granularity (not city/state)
- Based on phone number format, not actual location
- May not reflect current location (e.g., someone with a US number living abroad)

**Query Example**:
```sql
SELECT 
    handle.country,
    COUNT(*) AS contact_count
FROM handle
WHERE handle.country IS NOT NULL
GROUP BY handle.country
ORDER BY contact_count DESC;
```

**Visualization Opportunities**:
- **World Map**: Country distribution of contacts
- **Bar Chart**: Top countries by contact count
- **Pie Chart**: Country breakdown percentage
- **Timeline**: Country distribution over time (if tracking changes)

---

#### 2. Physical Addresses (Contacts Database)

**Source**: `ZABCDPOSTALADDRESS` table in Contacts database

**Location**: `~/Library/Application Support/AddressBook/AddressBook-v22.abcddb`

**What it contains**:
- Street addresses
- City, state/province, postal code
- Country
- Address type (home, work, other)

**Access Method**:
```python
import sqlite3
from pathlib import Path

contacts_db = Path.home() / "Library/Application Support/AddressBook/AddressBook-v22.abcddb"

conn = sqlite3.connect(f"file:{contacts_db}?mode=ro", uri=True)

# Get addresses for contacts
cursor = conn.execute("""
    SELECT 
        r.ZFIRSTNAME || ' ' || r.ZLASTNAME AS name,
        a.ZSTREET,
        a.ZCITY,
        a.ZSTATE,
        a.ZZIPCODE,
        a.ZCOUNTRY,
        a.ZLABEL  -- 'home', 'work', etc.
    FROM ZABCDRECORD r
    JOIN ZABCDPOSTALADDRESS a ON r.Z_PK = a.ZOWNER
    WHERE a.ZSTREET IS NOT NULL
""")
```

**Linking to chat.db**:
```sql
-- Link contacts to handles via phone/email
SELECT 
    chat.display_name,
    handle.id,
    -- Join to Contacts DB to get address
    contact_address.ZCITY,
    contact_address.ZSTATE,
    contact_address.ZCOUNTRY
FROM chat
JOIN handle ON chat.chat_identifier = handle.id
-- Then join to Contacts DB (requires separate connection)
```

**Visualization Opportunities**:
- **Geographic Map**: Plot contacts by address on world map
- **City Distribution**: Bar chart of cities
- **Distance Analysis**: Calculate distances between contacts
- **Regional Clusters**: Group contacts by region/state
- **Travel Patterns**: If tracking address changes over time

**Privacy Note**: Physical addresses are sensitive data - handle with care.

---

#### 3. Shared Location URLs (Message Text)

**Source**: `message.text` field containing Apple Maps URLs

**What it contains**:
- When users share their location via iMessage, it creates a message with an Apple Maps URL
- URL format: `https://maps.apple.com/?ll=LATITUDE,LONGITUDE` or `http://maps.apple.com/?ll=LATITUDE,LONGITUDE`
- Coordinates are embedded in the URL query parameters
- May also include address information in the URL

**Query Example**:
```sql
SELECT 
    message.ROWID,
    message.text,
    message.date,
    chat.display_name,
    message.is_from_me
FROM message
JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
JOIN chat ON chat_message_join.chat_id = chat.ROWID
WHERE message.text LIKE '%maps.apple.com%'
   OR message.text LIKE '%maps.google.com%'
ORDER BY message.date DESC;
```

**Extracting Coordinates**:
```python
import re
from urllib.parse import urlparse, parse_qs

def extract_location_from_message(text: str) -> dict | None:
    """Extract GPS coordinates from Apple Maps URL in message text."""
    if not text:
        return None
    
    # Look for Apple Maps URLs
    apple_maps_pattern = r'https?://maps\.apple\.com/\?.*ll=([0-9.-]+),([0-9.-]+)'
    match = re.search(apple_maps_pattern, text)
    
    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        return {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'shared_location',
            'url': match.group(0)
        }
    
    # Also check for Google Maps URLs (less common in iMessage)
    google_maps_pattern = r'https?://(?:www\.)?google\.com/maps.*@([0-9.-]+),([0-9.-]+)'
    match = re.search(google_maps_pattern, text)
    
    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        return {
            'latitude': latitude,
            'longitude': longitude,
            'source': 'google_maps_share',
            'url': match.group(0)
        }
    
    return None

# Usage
query = """
    SELECT message.text, message.date, chat.display_name
    FROM message
    JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
    JOIN chat ON chat_message_join.chat_id = chat.ROWID
    WHERE message.text LIKE '%maps.apple.com%'
"""

for row in db.execute_query(query):
    text, date, display_name = row
    location = extract_location_from_message(text)
    if location:
        print(f"Location shared by {display_name} at {date}: {location['latitude']}, {location['longitude']}")
```

**Visualization Opportunities**:
- **Shared Location Map**: Plot all shared locations on a map
- **Location Sharing Timeline**: When locations were shared over time
- **Location by Contact**: Who shares locations most frequently
- **Location Clusters**: Frequently shared locations
- **Travel Path**: Connect shared locations chronologically

**Privacy Considerations**:
- Shared locations are explicit user actions (less sensitive than photo EXIF)
- Still requires privacy considerations
- Users intentionally shared these locations

---

#### 4. GPS Coordinates (Photo EXIF Data)

**Source**: EXIF metadata in photo attachments

**Location**: Attachment files in `~/Library/Messages/Attachments/`

**What it contains**:
- Latitude and longitude coordinates
- Altitude (sometimes)
- Timestamp of when photo was taken
- Camera/device information

**Extraction Method**:

**Option 1: Using Python (Pillow/Piexif)**:
```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os

def get_gps_from_image(image_path):
    """Extract GPS coordinates from image EXIF data."""
    try:
        image = Image.open(image_path)
        exif = image._getexif()
        
        if exif is None:
            return None
            
        # Find GPS info
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'GPSInfo':
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag] = gps_value
                
                # Convert to decimal degrees
                lat = gps_data.get('GPSLatitude')
                lon = gps_data.get('GPSLongitude')
                if lat and lon:
                    lat_ref = gps_data.get('GPSLatitudeRef', 'N')
                    lon_ref = gps_data.get('GPSLongitudeRef', 'E')
                    
                    lat_decimal = convert_to_decimal(lat, lat_ref)
                    lon_decimal = convert_to_decimal(lon, lon_ref)
                    
                    return {
                        'latitude': lat_decimal,
                        'longitude': lon_decimal,
                        'altitude': gps_data.get('GPSAltitude')
                    }
    except Exception as e:
        print(f"Error reading EXIF: {e}")
    return None

def convert_to_decimal(coord, ref):
    """Convert DMS (degrees, minutes, seconds) to decimal."""
    degrees, minutes, seconds = coord
    decimal = degrees + minutes/60.0 + seconds/3600.0
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal
```

**Option 2: Using exiftool (command line)**:
```bash
# Install: brew install exiftool
exiftool -GPSLatitude -GPSLongitude -GPSAltitude /path/to/image.jpg
```

**Finding Attachment Files**:
```python
# Attachment files are stored with GUID-based names
# Path: ~/Library/Messages/Attachments/
# Filename pattern: {guid}/{filename}

attachment_dir = Path.home() / "Library/Messages/Attachments"

# Query attachment metadata from database
query = """
    SELECT 
        attachment.guid,
        attachment.filename,
        attachment.created_date,
        message.date AS message_date,
        chat.display_name
    FROM attachment
    JOIN message_attachment_join ON attachment.ROWID = message_attachment_join.attachment_id
    JOIN message ON message_attachment_join.message_id = message.ROWID
    JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
    JOIN chat ON chat_message_join.chat_id = chat.ROWID
    WHERE attachment.mime_type LIKE 'image/%'
    ORDER BY attachment.created_date DESC
"""

# Then find file and extract GPS
for row in results:
    guid, filename, created_date, message_date, display_name = row
    file_path = attachment_dir / guid / filename
    if file_path.exists():
        gps = get_gps_from_image(file_path)
        if gps:
            # Store GPS data for visualization
            pass
```

**Visualization Opportunities**:
- **Photo Map**: Plot photos on world map by GPS coordinates
- **Location Timeline**: Show where photos were taken over time
- **Location Heatmap**: Density map of photo locations
- **Travel Path**: Connect photo locations chronologically
- **Location by Contact**: Where photos were shared with each contact
- **Location Clusters**: Identify frequently visited places

**Privacy Considerations**:
- GPS coordinates are highly sensitive
- Many users may have location services disabled
- Photos may not always have GPS data (screenshots, downloaded images)
- Consider opt-in/opt-out for location-based features

---

#### 5. Time Zone Inference

**Source**: Activity patterns and message timestamps

**What it can tell you**:
- Approximate time zone based on activity patterns
- When contacts are most active (suggests their time zone)
- Travel patterns (if activity shifts to different hours)

**Method**:
```python
# Analyze activity patterns to infer time zones
# If someone is consistently active at 2-4 AM your time,
# they might be in a different time zone

query = """
    SELECT 
        chat.display_name,
        CAST(strftime('%H', 
            datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), 
                    "unixepoch", "localtime")) AS INTEGER) AS hour_of_day,
        COUNT(*) AS message_count
    FROM message
    JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
    JOIN chat ON chat_message_join.chat_id = chat.ROWID
    WHERE message.is_from_me = 0
    GROUP BY chat.display_name, hour_of_day
    ORDER BY message_count DESC
"""
```

**Limitations**:
- Not precise (people have different sleep schedules)
- Doesn't account for night shifts, travel, etc.
- Only suggests time zone, doesn't confirm location

---

### Location Data Summary

| Data Source | Granularity | Availability | Privacy Level |
|------------|-------------|--------------|---------------|
| `handle.country` | Country | High (most contacts) | Low sensitivity |
| `message.country` | Country | Medium | Low sensitivity |
| **Shared Location URLs** | **Precise coordinates** | **Medium (when shared)** | **Medium sensitivity** |
| Contacts addresses | Street/City | Medium (if in Contacts) | High sensitivity |
| Photo EXIF GPS | Precise coordinates | Low (only photos with location) | Very high sensitivity |
| Time zone inference | Approximate | High | Low sensitivity |

---

### Visualization Components for Location

#### `CountryDistribution`
**Purpose**: Show contact distribution by country

**Data**: `handle.country` aggregated counts

**Visualization**: 
- World map with country shading
- Bar chart of top countries
- Pie chart percentage breakdown

**API Endpoint**: `/stats/countries`

---

#### `ContactMap`
**Purpose**: Plot contacts on map by address

**Data**: Contacts database `ZABCDPOSTALADDRESS` joined to `handle`

**Visualization**:
- Interactive map (Google Maps, Mapbox, Leaflet)
- Markers for each contact
- Clustering for dense areas
- Click marker to see contact info

**API Endpoint**: `/contacts/map`

**Privacy**: Requires explicit opt-in, anonymize for export

---

#### `SharedLocationMap`
**Purpose**: Show locations shared via iMessage

**Data**: GPS coordinates extracted from Apple Maps URLs in `message.text`

**Visualization**:
- Map with location markers
- Timeline slider to show shared locations over time
- Heatmap of shared location density
- Travel path connecting shared locations chronologically
- Location by Contact: Who shared locations and when
- Location Clusters: Frequently shared locations

**API Endpoint**: `/messages/shared-locations`

**Privacy**: Medium sensitivity - users explicitly shared these

---

#### `PhotoLocationMap`
**Purpose**: Show where photos were taken

**Data**: GPS coordinates extracted from photo EXIF data

**Visualization**:
- Map with photo markers
- Timeline slider to show photos over time
- Heatmap of photo density
- Travel path connecting photos chronologically

**API Endpoint**: `/attachments/locations`

**Privacy**: Very sensitive - require explicit consent

---

#### `LocationTimeline`
**Purpose**: Show location activity over time

**Data**: GPS coordinates with timestamps

**Visualization**:
- Timeline with location markers
- Map view synchronized with timeline
- Filter by contact or date range

---

### Implementation Considerations

1. **Privacy First**:
   - Location data is highly sensitive
   - Require explicit opt-in for location features
   - Anonymize data for exports
   - Clear privacy warnings

2. **Performance**:
   - EXIF extraction is slow (process in background)
   - Cache GPS coordinates after extraction
   - Use geocoding services sparingly (rate limits)

3. **Data Quality**:
   - Not all photos have GPS data
   - Country codes may be inaccurate
   - Addresses may be outdated
   - Validate and handle missing data gracefully

4. **Geocoding**:
   - Convert addresses to coordinates: Google Geocoding API, Mapbox, OpenStreetMap
   - Cache results (addresses don't change often)
   - Handle API rate limits

---

### Query Examples

#### Get Country Distribution
```sql
SELECT 
    handle.country,
    COUNT(DISTINCT handle.ROWID) AS contact_count,
    COUNT(*) AS message_count
FROM handle
JOIN message ON handle.ROWID = message.handle_id
WHERE handle.country IS NOT NULL
GROUP BY handle.country
ORDER BY contact_count DESC;
```

#### Get Messages by Country
```sql
SELECT 
    message.country,
    COUNT(*) AS message_count,
    MIN(datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime")) AS first_message,
    MAX(datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime")) AS last_message
FROM message
WHERE message.country IS NOT NULL
GROUP BY message.country;
```

#### Get Shared Locations from Messages
```sql
SELECT 
    message.ROWID,
    message.text,
    message.date,
    chat.display_name,
    message.is_from_me,
    datetime(message.date / 1000000000 + strftime("%s", "2001-01-01"), "unixepoch", "localtime") AS readable_date
FROM message
JOIN chat_message_join ON message.ROWID = chat_message_join.message_id
JOIN chat ON chat_message_join.chat_id = chat.ROWID
WHERE message.text LIKE '%maps.apple.com%'
   OR message.text LIKE '%maps.google.com%'
ORDER BY message.date DESC;
```

**Note**: Coordinates need to be extracted from URLs using regex/parsing (see Python example above).

---

#### Get Contacts with Addresses (requires Contacts DB join)
```python
# This requires joining two databases
contacts_db = sqlite3.connect(f"file:{contacts_db_path}?mode=ro", uri=True)
chat_db = sqlite3.connect(f"file:{chat_db_path}?mode=ro", uri=True)

# Get handles from chat.db
handles = chat_db.execute("SELECT id, person_centric_id FROM handle").fetchall()

# For each handle, try to find address in Contacts DB
for handle_id, person_id in handles:
    if person_id:
        # Use person_centric_id to find contact
        address = contacts_db.execute("""
            SELECT ZSTREET, ZCITY, ZSTATE, ZZIPCODE, ZCOUNTRY
            FROM ZABCDPOSTALADDRESS
            WHERE ZOWNER = (SELECT Z_PK FROM ZABCDRECORD WHERE Z_PK = ?)
            LIMIT 1
        """, (person_id,)).fetchone()
```

---

## References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [iMessage Database Analysis](https://stmorse.github.io/journal/iMessage.html)
- [Mac Address Book Schema](https://michaelwornow.net/2024/12/24/mac-address-book-schema)
- [EXIF GPS Data Extraction](https://www.makeuseof.com/how-to-view-exif-metadata-on-mac/)

---

*Last Updated: 2025-12-17*
*Database Schema Version: Based on macOS Messages app*
