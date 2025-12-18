# React Component Architecture

Comprehensive component design for the iMessage Analysis frontend, based on thorough database analysis.

## Component Categories

### 1. Dashboard & Overview Components
### 2. Time-Based Activity Components
### 3. Contact & Relationship Components
### 4. Content Analysis Components
### 5. Media & Attachment Components
### 6. Group Chat Components
### 7. Search & Filter Components
### 8. Individual Chat Detail Components
### 9. Utility & Layout Components

---

## 1. Dashboard & Overview Components

### `DashboardOverview`
**Purpose**: High-level summary with key metrics

**Data Needed**:
- Total messages, chats, contacts
- Date range (first/last message)
- Service breakdown (iMessage vs SMS)
- Recent activity summary

**Features**:
- Stat cards (messages, chats, contacts, date range)
- Service pie chart (iMessage vs SMS)
- Quick stats (avg messages/day, most active day)
- Last updated timestamp

**API Endpoint**: `/summary` (exists)

---

### `StatCard`
**Purpose**: Reusable card for displaying a single metric

**Props**:
```typescript
{
  label: string;
  value: number | string;
  subtitle?: string;
  trend?: { value: number; direction: 'up' | 'down' };
  icon?: ReactNode;
}
```

**Use Cases**: Messages count, chats count, contacts count, storage used

---

### `ServiceBreakdown`
**Purpose**: Visual breakdown of iMessage vs SMS usage

**Data Needed**:
- Count of messages by `service` field
- Percentage breakdown

**Visualization**: Pie chart or donut chart

**API Endpoint**: `/stats/service-breakdown` (needs to be created)

---

## 2. Time-Based Activity Components

### `ActivityTimeline`
**Purpose**: Messages over time (line chart)

**Data Needed**:
- Messages per day/hour/week (aggregated by date)
- Optional filters: contact, service, read status

**Features**:
- Time range selector (last week, month, year, all time)
- Granularity selector (day, week, month)
- Interactive tooltips
- Zoom/pan capability

**API Endpoint**: `/stats/activity-timeline?start_date=&end_date=&granularity=day`

**Visualization**: Line chart (Plotly or Recharts)

---

### `ActivityHeatmap`
**Purpose**: Activity by hour-of-day × day-of-week

**Data Needed**:
- Message counts grouped by:
  - Hour of day (0-23)
  - Day of week (0-6)
- Color intensity based on count

**Features**:
- Hover tooltips showing exact counts
- Color scale legend
- Optional: filter by contact or service

**API Endpoint**: `/stats/activity-heatmap?contact_id=`

**Visualization**: 2D heatmap (7×24 grid)

**Priority**: High (mentioned in roadmap v0.4)

---

### `ActivityCalendar`
**Purpose**: Calendar view showing message activity per day

**Data Needed**:
- Messages per day
- Streaks (consecutive days with messages)
- Peak months

**Features**:
- Month/year navigation
- Color intensity for activity
- Click to see day details
- Streak indicators

**API Endpoint**: `/stats/activity-calendar?year=&month=`

**Visualization**: Calendar grid with color coding

---

### `ReplyTimeAnalysis`
**Purpose**: Analysis of response times

**Data Needed**:
- Time-to-reply: `date_read - date` (for messages not from me)
- Grouped by contact, hour, day of week

**Features**:
- Reply time distribution (histogram)
- Median/p95 reply times per contact
- Reply time heatmap (hour × day of week)
- Fastest/slowest responders

**API Endpoint**: `/stats/reply-times?contact_id=`

**Visualization**: 
- Histogram for distribution
- Heatmap for patterns
- Box plot for per-contact comparison

**Priority**: High (mentioned in roadmap v0.5)

---

### `TimeOfDayFingerprint`
**Purpose**: Show when each contact is most active (24-hour distribution)

**Data Needed**:
- Message counts per hour (0-23) per contact
- Normalized percentages

**Features**:
- Stacked area chart or multiple line charts
- Compare multiple contacts
- Identify "night owls" vs "early birds"

**API Endpoint**: `/stats/time-of-day?contact_ids=`

**Visualization**: Stacked area chart or radar chart

---

## 3. Contact & Relationship Components

### `ContactList`
**Purpose**: List all contacts with key stats

**Data Needed**:
- Contact info (display_name, chat_identifier, handle_id)
- Message count per contact
- Last message date
- Service preferences

**Features**:
- Sortable columns
- Search/filter
- Click to view contact detail
- Avatar placeholders (future: profile photos from Contacts DB)

**API Endpoint**: `/contacts` (needs enhancement)

---

### `ContactCard`
**Purpose**: Individual contact summary card

**Props**:
```typescript
{
  contact: {
    display_name: string;
    chat_identifier: string;
    message_count: number;
    last_message_date: string;
    service_preference: 'iMessage' | 'SMS' | 'mixed';
  };
  onClick?: () => void;
}
```

**Features**:
- Contact name (with fallback to identifier)
- Message count
- Last activity
- Service indicator
- Quick stats preview

---

### `ContactNetworkGraph`
**Purpose**: Visualize relationships between contacts

**Data Needed**:
- Group chat memberships (`chat_handle_join`)
- Co-occurrence in group chats

**Features**:
- Force-directed graph
- Nodes = contacts
- Edges = appear in same group chat
- Node size = message count
- Edge thickness = number of shared groups
- Interactive: click to focus, drag nodes

**API Endpoint**: `/network/contact-graph`

**Visualization**: Network graph (D3.js or vis.js)

**Priority**: Medium (mentioned in roadmap)

---

### `TopContacts`
**Purpose**: Bar chart of top contacts by message count

**Data Needed**:
- Top N contacts with message counts
- Optional: filter by time range

**Features**:
- Horizontal bar chart
- Click to drill down
- Show percentage of total
- Limit selector (top 10, 25, 50)

**API Endpoint**: `/top-chats` (exists, needs enhancement)

**Visualization**: Horizontal bar chart

---

### `ContactComparison`
**Purpose**: Compare multiple contacts side-by-side

**Data Needed**:
- Selected contacts' stats
- Message counts, reply times, activity patterns

**Features**:
- Multi-select contact picker
- Side-by-side stat cards
- Overlay charts (activity timelines)
- Export comparison

**API Endpoint**: `/contacts/compare?ids=`

---

## 4. Content Analysis Components

### `MessageLengthDistribution`
**Purpose**: Histogram of message lengths

**Data Needed**:
- Message text lengths (`LENGTH(text)`)
- Grouped into bins

**Features**:
- Histogram with adjustable bin size
- Filter by contact
- Show median, mean, outliers
- Longest messages list

**API Endpoint**: `/stats/message-lengths?contact_id=`

**Visualization**: Histogram

**Priority**: High (mentioned in roadmap v0.5)

---

### `WordCloud`
**Purpose**: Visual word frequency

**Data Needed**:
- Word frequencies from message text
- Filtered (stop words, common words)

**Features**:
- Size = frequency
- Color = contact or random
- Click word to search
- Filter by contact or time range

**API Endpoint**: `/content/word-frequencies?contact_id=&limit=100`

**Visualization**: Word cloud (react-wordcloud or custom)

---

### `KeywordTrends`
**Purpose**: Track specific keywords over time

**Data Needed**:
- Message counts containing keywords
- Grouped by date
- Configurable keyword list

**Features**:
- Add/remove keywords
- Time series for each keyword
- Multiple keywords on same chart
- Case-insensitive matching

**API Endpoint**: `/content/keyword-trends?keywords=`

**Visualization**: Multi-line chart

---

### `EmojiUsage`
**Purpose**: Analyze emoji usage patterns

**Data Needed**:
- Emoji frequencies
- Emoji usage over time
- Per-contact emoji preferences

**Features**:
- Top emojis list
- Emoji timeline
- Per-contact breakdown
- Emoji diversity score

**API Endpoint**: `/content/emoji-stats?contact_id=`

**Visualization**: Bar chart + timeline

---

### `SentimentAnalysis`
**Purpose**: Sentiment trends (if implemented)

**Data Needed**:
- Sentiment scores per message
- Aggregated by date/contact

**Features**:
- Sentiment timeline
- Positive/negative/neutral breakdown
- Per-contact sentiment

**API Endpoint**: `/content/sentiment?contact_id=`

**Visualization**: Area chart (positive/negative stacked)

**Priority**: Low (requires ML/NLP)

---

## 5. Media & Attachment Components

### `AttachmentStats`
**Purpose**: Overview of attachments

**Data Needed**:
- Total attachments
- Total storage (bytes)
- Attachments per chat
- Type breakdown (mime_type)

**Features**:
- Storage usage card
- Attachment count card
- Type distribution pie chart

**API Endpoint**: `/attachments/stats`

---

### `AttachmentTypeBreakdown`
**Purpose**: Pie chart of attachment types

**Data Needed**:
- Count by `mime_type` (image/jpeg, video/mp4, etc.)
- Storage by type

**Features**:
- Interactive pie chart
- Click slice to filter
- Storage vs count toggle

**API Endpoint**: `/attachments/types`

**Visualization**: Pie chart

---

### `AttachmentTimeline`
**Purpose**: Attachments shared over time

**Data Needed**:
- Attachments per day
- Grouped by type or contact

**Features**:
- Time series line chart
- Stacked by type
- Filter by contact

**API Endpoint**: `/attachments/timeline?start_date=&end_date=`

**Visualization**: Stacked area chart

---

### `StorageUsage`
**Purpose**: Storage breakdown by contact/chat

**Data Needed**:
- `total_bytes` per chat/contact
- Cumulative storage over time

**Features**:
- Bar chart (storage per contact)
- Timeline (cumulative)
- Top storage users

**API Endpoint**: `/attachments/storage?group_by=contact`

**Visualization**: Bar chart + line chart

---

## 6. Group Chat Components

### `GroupChatList`
**Purpose**: List all group chats

**Data Needed**:
- Group chats (where `room_name` is not NULL)
- Participant count
- Message count
- Last activity

**Features**:
- Sortable table
- Participant count column
- Click to view group detail

**API Endpoint**: `/groups/list`

---

### `GroupChatDetail`
**Purpose**: Detailed view of a single group chat

**Data Needed**:
- Group info (room_name, participants)
- Message stats
- Participant activity
- Timeline

**Features**:
- Participant list with message counts
- Activity timeline
- Participant activity breakdown
- Group actions timeline (add/remove members)

**API Endpoint**: `/groups/:group_id`

---

### `GroupChatNetwork`
**Purpose**: Visualize group chat relationships

**Data Needed**:
- Group chat memberships
- Participant connections

**Features**:
- Network graph
- Nodes = contacts
- Edges = shared group chats
- Highlight "hubs" (most connected)

**API Endpoint**: `/network/group-graph`

**Visualization**: Network graph

---

### `GroupActivityTimeline`
**Purpose**: Activity in group chats over time

**Data Needed**:
- Messages per group per day
- Participant contributions

**Features**:
- Stacked area chart (one series per group)
- Or: heatmap (group × date)
- Filter by date range

**API Endpoint**: `/groups/activity-timeline`

**Visualization**: Stacked area or heatmap

---

## 7. Search & Filter Components

### `MessageSearch`
**Purpose**: Search messages by text content

**Data Needed**:
- Full-text search results
- Match counts over time

**Features**:
- Search input
- Results list
- Match highlighting
- Time filter
- Contact filter

**API Endpoint**: `/search?q=&contact_id=&start_date=`

**Priority**: High (mentioned in roadmap)

---

### `FilterPanel`
**Purpose**: Reusable filter component

**Props**:
```typescript
{
  filters: {
    contacts?: string[];
    dateRange?: { start: Date; end: Date };
    service?: 'iMessage' | 'SMS' | 'all';
    readStatus?: 'read' | 'unread' | 'all';
  };
  onFilterChange: (filters: FilterState) => void;
}
```

**Features**:
- Contact multi-select
- Date range picker
- Service selector
- Read status toggle
- Clear all button

---

### `DateRangePicker`
**Purpose**: Select date range for analysis

**Features**:
- Start/end date inputs
- Preset ranges (last week, month, year, all time)
- Calendar picker
- Relative date selector

---

## 8. Individual Chat Detail Components

### `ChatDetail`
**Purpose**: Comprehensive view of a single chat

**Data Needed**:
- Chat info (display_name, chat_identifier)
- All messages in chat
- Stats (message count, character count, reply times)
- Timeline

**Features**:
- Chat header with stats
- Message list (virtualized for performance)
- Stats cards
- Activity timeline
- Export option

**API Endpoint**: `/chats/:chat_identifier`

---

### `ChatStats`
**Purpose**: Statistics for a single chat

**Data Needed**:
- Message count (from me vs others)
- Character count
- Reply time stats
- First/last message dates
- Active periods

**Features**:
- Balance indicator (you vs them %)
- Reply time metrics
- Activity timeline
- Longest silence gap

**API Endpoint**: `/chats/:chat_identifier/stats`

**Priority**: High (mentioned in roadmap v0.5)

---

### `ConversationBalance`
**Purpose**: Visualize message balance over time

**Data Needed**:
- Messages per month
- Split by `is_from_me`

**Features**:
- Stacked bar chart (you vs them)
- Percentage over time
- Monthly breakdown

**API Endpoint**: `/chats/:chat_identifier/balance`

**Visualization**: Stacked bar chart

**Priority**: High (mentioned in roadmap v0.4)

---

### `MessageList`
**Purpose**: Scrollable list of messages

**Props**:
```typescript
{
  messages: LatestMessage[];
  onLoadMore?: () => void;
  virtualized?: boolean;
}
```

**Features**:
- Virtual scrolling (for large lists)
- Infinite scroll
- Message grouping by date
- Read receipts display
- Attachment indicators

---

### `MessageThread`
**Purpose**: Show reply chains

**Data Needed**:
- Messages with `reply_to_guid` or `thread_originator_guid`
- Thread relationships

**Features**:
- Nested message display
- Thread depth indicator
- Expand/collapse threads
- Thread visualization

**API Endpoint**: `/chats/:chat_identifier/threads`

**Visualization**: Nested tree view

---

## 9. Utility & Layout Components

### `TabNavigation`
**Purpose**: Main navigation tabs

**Tabs**:
- Overview
- Activity
- Contacts
- Groups
- Search
- Settings

**Features**:
- Active tab highlighting
- URL routing (optional)
- Badge indicators (e.g., unread count)

---

### `LoadingSpinner`
**Purpose**: Loading state indicator

**Features**:
- Centered spinner
- Optional message
- Skeleton loaders for content

---

### `ErrorBoundary`
**Purpose**: Catch and display errors gracefully

**Features**:
- Error message
- Retry button
- Error details (dev mode)

---

### `DataTable`
**Purpose**: Reusable sortable/filterable table

**Props**:
```typescript
{
  columns: Column[];
  data: any[];
  sortable?: boolean;
  filterable?: boolean;
  paginated?: boolean;
}
```

**Features**:
- Column sorting
- Column filtering
- Pagination
- Row selection
- Export to CSV

---

### `ChartContainer`
**Purpose**: Wrapper for charts with common features

**Features**:
- Title
- Legend
- Export button (PNG, SVG)
- Fullscreen toggle
- Tooltip configuration

---

## Component Hierarchy

```
App
├── TabNavigation
├── DashboardOverview
│   ├── StatCard (×4)
│   ├── ServiceBreakdown
│   └── QuickStats
├── ActivityView
│   ├── ActivityTimeline
│   ├── ActivityHeatmap
│   ├── ActivityCalendar
│   └── ReplyTimeAnalysis
├── ContactsView
│   ├── ContactList
│   ├── TopContacts
│   ├── ContactNetworkGraph
│   └── ContactComparison
├── GroupsView
│   ├── GroupChatList
│   ├── GroupChatDetail
│   └── GroupChatNetwork
├── SearchView
│   ├── MessageSearch
│   └── FilterPanel
└── ChatDetailView
    ├── ChatStats
    ├── ConversationBalance
    ├── MessageList
    └── MessageThread
```

---

## Implementation Priority

### Phase 1: Core Dashboard (MVP)
1. ✅ `DashboardOverview` (exists, needs enhancement)
2. ✅ `TopContacts` (exists, needs enhancement)
3. `ActivityTimeline` - High priority (roadmap v0.4)
4. `ActivityHeatmap` - High priority (roadmap v0.4)
5. `ConversationBalance` - High priority (roadmap v0.4)

### Phase 2: Contact Analysis
6. `ContactList` - Enhanced version
7. `ContactCard` - Reusable component
8. `ReplyTimeAnalysis` - High priority (roadmap v0.5)
9. `MessageLengthDistribution` - High priority (roadmap v0.5)

### Phase 3: Advanced Features
10. `MessageSearch` - High priority (roadmap)
11. `GroupChatList` - Medium priority
12. `AttachmentStats` - Medium priority
13. `WordCloud` - Low priority
14. `ContactNetworkGraph` - Low priority

### Phase 4: Polish & Performance
15. Virtual scrolling for large lists
16. Chart export functionality
17. Advanced filtering
18. Data export (CSV, PDF)

---

## Data Requirements Summary

### New API Endpoints Needed

1. `/stats/activity-timeline` - Time series data
2. `/stats/activity-heatmap` - Hour × day matrix
3. `/stats/reply-times` - Reply time analysis
4. `/stats/message-lengths` - Length distribution
5. `/chats/:id` - Individual chat detail
6. `/chats/:id/stats` - Chat statistics
7. `/chats/:id/balance` - Conversation balance
8. `/contacts` - Enhanced contact list
9. `/attachments/stats` - Attachment overview
10. `/groups/list` - Group chat list
11. `/search` - Message search
12. `/content/word-frequencies` - Word analysis
13. `/content/emoji-stats` - Emoji analysis

---

## Technology Recommendations

### Charting Libraries
- **Plotly.js** (or react-plotly.js) - Most powerful, good for complex charts
- **Recharts** - React-native, good for simple charts
- **Victory** - Good for interactive charts
- **Chart.js** - Lightweight, good for basic charts

**Recommendation**: Start with **Recharts** for simplicity, migrate to **Plotly.js** for advanced features.

### Data Visualization
- **D3.js** - For custom visualizations (network graphs, word clouds)
- **vis.js** - For network graphs
- **react-wordcloud** - For word clouds

### UI Components
- **React Router** - For navigation/routing
- **React Virtual** - For virtual scrolling
- **date-fns** - For date manipulation
- **react-select** - For multi-select filters

---

## Performance Considerations

1. **Virtual Scrolling**: Use for message lists > 100 items
2. **Pagination**: For large datasets (contacts, messages)
3. **Lazy Loading**: Load charts on demand
4. **Memoization**: Use React.memo for expensive components
5. **Data Aggregation**: Do heavy aggregation on backend
6. **Caching**: Cache API responses for static data
7. **Debouncing**: For search and filter inputs

---

## Accessibility

1. **Keyboard Navigation**: All interactive elements
2. **Screen Reader Support**: ARIA labels
3. **Color Contrast**: WCAG AA compliance
4. **Focus Indicators**: Visible focus states
5. **Alt Text**: For charts and images

---

*Last Updated: 2025-12-17*
*Based on: CHATDB.md database analysis*
