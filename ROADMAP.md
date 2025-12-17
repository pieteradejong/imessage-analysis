# ROADMAP

## Vision
A locally-run iMessage analysis app that:
- Safely ingests your iMessage `chat.db` (never mutates Apple’s DB)
- Produces useful, “interesting” metrics and visualizations
- Supports repeatable runs against timestamped snapshots for reproducibility

## Product constraints / principles
- **Local-first & private**: no network required; no data leaves your machine.
- **Read-only source**: treat `~/Library/Messages/chat.db` as immutable.
- **Reproducible analysis**: every run can be tied to a snapshot timestamp.
- **Fast iteration**: prefer in-memory reads for heavy aggregate queries.

## Current state (already built)
- **CLI entrypoint**: `main.py` (and `imessage-analysis` console script)
- **DB access**: `DatabaseConnection` read-only (`mode=ro`)
- **Basic analysis**:
  - Database summary (tables, counts)
  - Latest messages
  - Message counts per chat
  - Per-chat “from me vs others” message + character counts
- **Package structure**: `imessage_analysis/` with config/db/queries/analysis stubs for visualization

## MVP target (next)
A locally run tool that:
- Creates/uses **timestamped snapshots** (for repeatability)
- Optionally **loads the snapshot into RAM** for fast querying
- Generates at least 2–4 genuinely useful visualizations and saves them as HTML

## Near-term milestones

### Milestone v0.2 — Snapshot-first runs (ops foundation)
- **Timestamped snapshot creation** (SQLite backup-based, WAL-safe)
- **Run analysis against snapshot** by default (or via flag)
- **Basic snapshot management**: list, delete old snapshots, keep-last-N

### Milestone v0.3 — In-memory analysis mode (speed)
- **Load snapshot into RAM** (`:memory:` + SQLite backup)
- Benchmarks: time-to-first-summary, top-N chat stats, time-series aggregation

### Milestone v0.4 — First “interesting” visuals (report)
Generate an HTML report (Plotly) with:
- **Activity over time** (messages/day; optionally 7-day rolling)
- **Day-of-week × hour-of-day heatmap** (message frequency)
- **Top chats** (bar chart) + long-tail distribution
- **Conversation balance** (from-me vs others %) per top chats

### Milestone v0.5 — Deeper per-chat drilldowns
For a selected chat identifier:
- **Reply time distribution** (median/p95) + heatmap by hour/day
- **Message length distribution** (histogram, long-message outliers)
- **First/last message date** + active periods

## Analysis & visualization ideas backlog

### Conversation dynamics
- **Reply-time heatmap**: median/percentiles of time-to-reply by hour-of-day and day-of-week (per chat + overall)
- **Conversation balance**: % from you vs them over time (stacked bars by month)
- **Initiation rate**: who starts conversations after long gaps
- **Silence gaps**: longest gaps per chat; “lost touch” ranking

### Activity / seasonality
- **Activity calendar**: messages per day; streaks; peak months
- **Time-of-day fingerprint**: per contact distribution across 24h
- **Weekend vs weekday**: ratio per chat

### Content-style metrics (privacy-conscious)
- **Emoji usage trends**: per chat and over time
- **Keyword trends**: configurable list (e.g. “lol”, “sorry”, “congrats”)
- **Message length**: median and tail (top 1% longest messages)

### Attachments
- **Attachments per chat** and over time
- **Type breakdown**: image/video/audio/other via `mime_type` / `uti`
- **Storage footprint**: total bytes by chat and by type

### Social graph / networks
- **Contact graph**: nodes = handles, edges = co-membership in group chats
- **Group chat “hubs”**: most connected participants

### Search & exploration
- **Fuzzy search UI**: query text and show match counts over time
- **Topic explorer (lightweight)**: top unigrams/bigrams per chat (optional)

## “Load all the SQL” notes
- `app/db/*.sql` appears to be a captured **schema** for `chat.db` (tables/indexes/triggers).
- Some triggers reference functions that won’t exist in a plain SQLite environment.
- Recommended MVP interpretation:
  - **Load and run analysis SQL** (your own queries) against snapshots/in-memory DB
  - Treat schema SQL as **reference/documentation**, unless we explicitly build a separate “analysis DB” that selectively applies schema elements.

## Proposed MVP UX
- **CLI-first report generator** (fastest path):
  - `python main.py --snapshot --use-memory` prints summary + writes `reports/report_YYYYmmdd_HHMMSS.html`
- Optional later:
  - Local dashboard (Streamlit/Dash) for interactive exploration
