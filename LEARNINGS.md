# Learnings

This document captures key learnings and best practices discovered during the development of this project.

## SQL Injection Prevention

### The Problem

SQL injection attacks occur when user-supplied input is directly interpolated into SQL queries using string formatting (f-strings, `.format()`, `%` formatting). This allows attackers to inject malicious SQL code that can:
- Read sensitive data
- Modify or delete data
- Execute arbitrary commands

**Example of vulnerable code:**
```python
# ❌ VULNERABLE - Direct string interpolation
def get_messages(chat_id: str):
    query = f"SELECT * FROM messages WHERE chat_id = '{chat_id}'"
    cursor.execute(query)
```

An attacker could pass `chat_id = "1' OR '1'='1"` to retrieve all messages.

### The Solution: Parameterized Queries

**Always use parameterized queries** with `?` placeholders (SQLite) or `%s` placeholders (PostgreSQL/MySQL) and pass parameters separately to `execute()`.

**Example of secure code:**
```python
# ✅ SECURE - Parameterized query
def get_messages(chat_id: str):
    query = "SELECT * FROM messages WHERE chat_id = ?"
    cursor.execute(query, (chat_id,))
```

### SQLite-Specific Considerations

#### 1. Parameterized Values

SQLite supports parameterized queries for **values** (strings, numbers, etc.) in WHERE clauses, INSERT/UPDATE statements, etc. Always use `?` placeholders:

```python
# ✅ Good - Parameterized value
query = "SELECT * FROM messages WHERE text LIKE ?"
cursor.execute(query, (f"%{search_term}%",))

# ✅ Good - Parameterized limit
query = "SELECT * FROM messages ORDER BY date DESC LIMIT ?"
cursor.execute(query, (limit,))
```

#### 2. SQL Identifiers Cannot Be Parameterized

**SQL identifiers** (table names, column names, database names) **cannot be parameterized** in SQLite. SQLite does not support binding identifiers as parameters.

**This does NOT work:**
```python
# ❌ This will NOT work - SQLite doesn't support parameterizing identifiers
query = "SELECT * FROM ?"
cursor.execute(query, (table_name,))  # Error!
```

**Solution: Validate identifiers before interpolation**

Since identifiers can't be parameterized, we must:
1. Validate the identifier against a strict whitelist pattern
2. Only then safely interpolate it into the SQL string

**Example implementation:**
```python
import re

# Regex pattern for valid SQLite identifiers
# Must start with letter or underscore, followed by letters, digits, or underscores
_SQLITE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _require_sqlite_identifier(value: str, *, field_name: str) -> str:
    """
    Validate an identifier (e.g. table name) to prevent SQL injection.
    
    SQLite does not support binding identifiers as parameters, so we must validate
    before safely interpolating into SQL.
    """
    if not _SQLITE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value

# ✅ Good - Validated identifier
def columns_for_table(table_name: str) -> str:
    safe_table = _require_sqlite_identifier(table_name, field_name="table_name")
    return f"PRAGMA table_info('{safe_table}');"
```

### Patterns Used in This Project

#### Pattern 1: Parameterized Query Functions

Functions that accept user input as **values** return a tuple `(query_string, parameters_tuple)`:

```python
def get_latest_messages(limit: int = 10) -> Tuple[str, Tuple[Any, ...]]:
    query = """
        SELECT * FROM messages
        ORDER BY date DESC
        LIMIT ?;
    """
    return query, (int(limit),)

# Usage:
query, params = get_latest_messages(limit=20)
rows = db.execute_query(query, params)
```

#### Pattern 2: Validated Identifier Functions

Functions that accept user input as **identifiers** validate before interpolation:

```python
def columns_for_table(table_name: str) -> str:
    safe_table = _require_sqlite_identifier(table_name, field_name="table_name")
    return f"PRAGMA table_info('{safe_table}');"

# Usage:
query = columns_for_table("message")
rows = db.execute_query(query)  # No parameters needed
```

#### Pattern 3: Mixed Approach

Some functions need both validated identifiers and parameterized values:

```python
def get_row_counts(table_names: List[str]) -> str:
    if not table_names:
        return "SELECT 0;"
    
    query = "SELECT "
    for tn in table_names[:-1]:
        safe_tn = _require_sqlite_identifier(tn, field_name="table_name")
        query += f"(SELECT COUNT(*) FROM `{safe_tn}`), "
    safe_last = _require_sqlite_identifier(table_names[-1], field_name="table_name")
    query += f"(SELECT COUNT(*) FROM `{safe_last}`);"
    return query
```

### Key Takeaways

1. **Never use f-strings or string formatting for user input in SQL queries**
2. **Always use parameterized queries (`?` placeholders) for values**
3. **Validate identifiers (table/column names) with strict regex before interpolation**
4. **Return `(query, params)` tuples from query builder functions for clarity**
5. **Document which functions return parameterized queries vs validated identifiers**

### Files Fixed

- `imessage_analysis/queries.py` - Main package (already fixed in commit f5f60d0)
- `queries.py` - Legacy file (fixed in this session)
- `analysis.py` - Legacy file (fixed in this session)

### References

- [SQLite Parameterized Queries](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders)
- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [SQLite Identifier Names](https://www.sqlite.org/lang_keywords.html)

## SQLite Database Operations

### Creating Consistent Snapshots

When working with SQLite databases (especially `chat.db` from iMessage), you need to create consistent snapshots for reproducibility. Simply copying the database file is **not sufficient** if the database is in WAL (Write-Ahead Logging) mode, which iMessage uses.

**The Problem:**
- SQLite in WAL mode uses multiple files: `chat.db`, `chat.db-wal`, `chat.db-shm`
- Copying only `chat.db` can result in an inconsistent snapshot
- The WAL file contains uncommitted transactions

**The Solution: Use SQLite's Backup API**

SQLite provides a `backup()` method that creates a consistent snapshot regardless of WAL mode:

```python
import sqlite3
from contextlib import closing

def create_snapshot(source_path: Path, dest_path: Path):
    source_uri = f"file:{source_path}?mode=ro"  # Read-only to avoid locks
    
    with closing(sqlite3.connect(source_uri, uri=True)) as src_conn:
        with closing(sqlite3.connect(str(dest_path))) as dst_conn:
            src_conn.backup(dst_conn)  # Creates consistent snapshot
```

**Key Points:**
- Use `mode=ro` URI parameter to open source in read-only mode (avoids locking issues)
- The `backup()` API handles WAL files automatically
- Creates a fully consistent snapshot in a single file
- Works even if the source database is actively being written to

### Loading Databases into Memory

For faster query performance, especially with large databases, you can load a SQLite database entirely into RAM using an in-memory database (`:memory:`).

**The Approach:**
1. Open the source database (read-only)
2. Create an in-memory database connection
3. Use `backup()` to copy the entire database into memory

```python
def load_into_memory(source_path: Path) -> sqlite3.Connection:
    source_uri = f"file:{source_path}?mode=ro"
    
    with closing(sqlite3.connect(source_uri, uri=True)) as disk_conn:
        mem_conn = sqlite3.connect(":memory:")
        disk_conn.backup(mem_conn)  # Copy entire DB to memory
        return mem_conn
```

**Benefits:**
- **Much faster reads** - no disk I/O after initial load
- **Consistent snapshot** - the in-memory copy is frozen at load time
- **Safe for analysis** - can't accidentally modify the source database

**Trade-offs:**
- **Memory usage** - entire database must fit in RAM
- **Load time** - initial backup operation takes time (but only once)
- **Best for read-heavy workloads** - writes are slower in memory

### Read-Only Database Access

When analyzing production databases (like iMessage's `chat.db`), always open them in read-only mode to prevent accidental modifications:

```python
# Using URI syntax
uri = f"file:{db_path}?mode=ro"
conn = sqlite3.connect(uri, uri=True)
```

**Benefits:**
- Prevents accidental writes/deletes
- Allows reading even if another process has the DB open
- Safer for production data

## Project Structure & Tooling

### Python Package Structure

For a Python project that needs to be both:
- **Importable as a package** (`import imessage_analysis`)
- **Runnable as a CLI** (`imessage-analysis` command)

Use this structure:
```
project/
├── imessage_analysis/      # Package directory
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── ...
├── main.py                 # CLI entry point
├── setup.py                # Package definition
└── pyproject.toml          # Modern Python project config
```

**Key Files:**

1. **`setup.py`** - Defines console scripts:
   ```python
   entry_points={
       "console_scripts": [
           "imessage-analysis=main:main",
       ],
   }
   ```

2. **`pyproject.toml`** - Modern Python project configuration:
   - Dependencies
   - Build system
   - Tool configurations (black, mypy, pytest)

3. **Editable installs** - Use `pip install -e .` during development:
   - Changes to code are immediately available
   - No need to reinstall after every change

### Shell Scripts for Development

Create consistent shell scripts for common operations:

**`init.sh`** - Project setup:
- Verify Python version
- Create virtual environment
- Install dependencies (editable + dev extras)
- Install frontend dependencies if present

**`run.sh`** - Run development servers:
- Start backend (FastAPI/Uvicorn)
- Start frontend (Vite/React)
- Run both concurrently
- Handle cleanup on exit (Ctrl+C)

**`test.sh`** - Run quality checks:
- Code formatting (`black --check`)
- Type checking (`mypy`)
- Unit tests (`pytest`)

**Best Practices:**
- Use `set -euo pipefail` for strict error handling
- Use `trap` for cleanup (kill background processes on exit)
- Support environment variables for configuration
- Check prerequisites before running

### Type Safety with mypy

Use type hints throughout the codebase and run `mypy` for static type checking:

**Common Issues & Solutions:**

1. **Untyped third-party libraries** (e.g., `plotly`):
   ```python
   import plotly.express as px  # type: ignore[import-untyped]
   ```

2. **Generic collections need explicit types**:
   ```python
   # ❌ mypy infers as object
   analysis = {}
   
   # ✅ Explicit type
   analysis: Dict[str, Any] = {}
   ```

3. **Optional values need runtime checks**:
   ```python
   if not config.db_path_str:
       raise RuntimeError("Database path not configured")
   path = Path(config.db_path_str)  # Now mypy knows it's not None
   ```

### Code Formatting with black

Use `black` for consistent code formatting:
- Run `black .` to format all files
- Run `black --check .` in CI/tests to verify formatting
- Configure in `pyproject.toml`:
  ```toml
  [tool.black]
  target-version = ['py312']
  line-length = 100
  ```

## Full-Stack Development

### FastAPI Backend

FastAPI is excellent for local development APIs:

**Key Features:**
- Automatic OpenAPI/Swagger docs at `/docs`
- Type validation via Pydantic
- Async support (though we use sync for SQLite)
- CORS middleware for local frontend

**Pattern: Thin HTTP Layer**
```python
# Keep business logic separate from HTTP layer
from imessage_analysis.analysis import get_database_summary

@app.get("/summary")
def summary():
    db = _open_db()  # Handle DB connection/snapshotting
    return get_database_summary(db)  # Reuse existing functions
```

**Environment-Based Configuration:**
- Use environment variables for flags (`IMESSAGE_SNAPSHOT`, `IMESSAGE_USE_MEMORY`)
- Allow overriding database path via `IMESSAGE_DB_PATH`
- Keep API layer thin - delegate to existing analysis functions

### React + TypeScript Frontend

**API Client Pattern:**
```typescript
// src/api.ts - Centralized API client
const API_BASE = 'http://127.0.0.1:8000';

export async function getSummary() {
  const res = await fetch(`${API_BASE}/summary`);
  return res.json();
}
```

**Component Structure:**
- Separate API calls from UI components
- Use TypeScript interfaces for API responses
- Handle loading/error states

### Running Backend + Frontend Concurrently

Use shell script with process management:

```bash
# Start both processes in background
backend_process &
frontend_process &

# Store PIDs
BACKEND_PID=$!
FRONTEND_PID=$!

# Cleanup function
cleanup() {
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Wait for both
wait $BACKEND_PID $FRONTEND_PID
```

**Key Points:**
- Use `trap` to ensure cleanup on Ctrl+C
- Store PIDs to kill processes later
- Use `wait` to keep script running until processes exit
- Handle errors gracefully (`|| true` to avoid script failure)

## Process Management

### Graceful Shutdown

When running multiple processes (backend + frontend), ensure proper cleanup:

1. **Store process PIDs** when starting background jobs
2. **Define cleanup function** that kills all processes
3. **Register trap handlers** for common signals:
   - `EXIT` - normal exit
   - `INT` - Ctrl+C
   - `TERM` - termination signal

```bash
cleanup() {
    set +e  # Don't exit on error
    if [[ -n "${BACKEND_PID}" ]]; then
        kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    fi
    if [[ -n "${FRONTEND_PID}" ]]; then
        kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
    fi
}

trap cleanup EXIT INT TERM
```

### Environment Variables for Configuration

Use environment variables for runtime configuration:

```bash
# Defaults with override capability
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
```

**Benefits:**
- No need to modify scripts for different environments
- Easy to override for testing
- Consistent pattern across scripts

## iMessage Database Structure

### Key Tables

- **`message`** - Individual messages (text, date, is_from_me, handle_id)
- **`chat`** - Chat conversations (chat_identifier, display_name)
- **`handle`** - Contacts/phone numbers (id, country, service)
- **`chat_message_join`** - Many-to-many relationship between chats and messages
- **`chat_handle_join`** - Many-to-many relationship between chats and handles (for group chats)

### Date Handling

iMessage stores dates as nanoseconds since 2001-01-01:

```sql
-- Convert to readable datetime
datetime(
    message.date / 1000000000 + strftime("%s", "2001-01-01"),
    "unixepoch",
    "localtime"
) AS message_date
```

### Read-Only Access

Always access `chat.db` in read-only mode:
- Located at `~/Library/Messages/chat.db` on macOS
- May be locked by Messages app
- Read-only mode allows reading even when locked
- Never modify the original database

## Testing Strategy

### Test Structure

```
tests/
├── test_api_import.py      # Smoke tests for imports
├── test_queries.py         # Query builder tests
└── test_snapshot.py        # Snapshot functionality tests
```

### Test Types

1. **Smoke Tests** - Verify modules can be imported
2. **Query Tests** - Verify query builders return correct `(query, params)` tuples
3. **Unit Tests** - Test individual functions in isolation
4. **Integration Tests** - Test with real database (if available)

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=imessage_analysis

# Run specific test file
pytest tests/test_queries.py
```

## Key Takeaways

1. **Always use parameterized queries** for user input values
2. **Validate identifiers** before interpolating into SQL
3. **Use SQLite backup API** for consistent snapshots (WAL-safe)
4. **Load into memory** for faster read-heavy analysis
5. **Open production DBs read-only** to prevent accidents
6. **Use type hints + mypy** for catching errors early
7. **Format code with black** for consistency
8. **Keep API layer thin** - delegate to business logic
9. **Use shell scripts** for common development tasks
10. **Handle process cleanup** with trap handlers
