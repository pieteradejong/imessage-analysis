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

## Bash Scripting Best Practices

### Readable ANSI Color Codes

When using colors in bash scripts, choose colors that are readable on both light and dark terminal backgrounds. Here's a recommended color palette:

**Basic Colors:**
```bash
# Standard colors (readable on most terminals)
RED='\033[0;31m'        # Red for errors
GREEN='\033[0;32m'      # Green for success
YELLOW='\033[1;33m'     # Bright yellow for warnings
CYAN='\033[0;36m'       # Cyan for headers/info (more readable than blue)
NC='\033[0m'            # No Color (reset)
```

**Why Cyan Instead of Blue:**
- **Blue (`\033[0;34m`)** - Dark blue can be hard to read on dark terminal backgrounds
- **Cyan (`\033[0;36m`)** - More visible and readable on both light and dark backgrounds
- **Bright Cyan (`\033[1;36m`)** - Even more visible, but can be too bright for some terminals

**Extended Color Palette:**
```bash
# Additional useful colors
BLUE='\033[0;34m'       # Standard blue (use sparingly)
MAGENTA='\033[0;35m'    # Magenta/purple
WHITE='\033[1;37m'      # Bright white
GRAY='\033[0;90m'       # Gray for secondary text

# Bright variants (more visible)
BRIGHT_RED='\033[1;31m'
BRIGHT_GREEN='\033[1;32m'
BRIGHT_CYAN='\033[1;36m'
```

**Usage Pattern:**
```bash
#!/usr/bin/env bash

# Define colors at the top
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Helper functions
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Usage
print_header "Running Tests"
print_success "Test passed"
print_error "Test failed"
print_warning "This is a warning"
```

**Color Code Format:**
- `\033[0;XXm` - Standard intensity (normal)
- `\033[1;XXm` - Bright/bold intensity
- `\033[0m` - Reset to default color

**ANSI Color Codes:**
- `30` - Black
- `31` - Red
- `32` - Green
- `33` - Yellow
- `34` - Blue
- `35` - Magenta
- `36` - Cyan
- `37` - White

**Best Practices:**
1. **Use cyan for headers** - More readable than blue on dark backgrounds
2. **Use green for success** - Universally recognized as positive
3. **Use red for errors** - Universally recognized as negative
4. **Use yellow for warnings** - Draws attention without being alarming
5. **Always reset colors** - Use `${NC}` after colored text
6. **Test on different terminals** - Colors may render differently
7. **Provide fallback** - Scripts should work even if colors aren't supported

**Testing Color Readability:**
```bash
# Test all colors
for color in RED GREEN YELLOW CYAN BLUE MAGENTA; do
  echo -e "${!color}This is $color${NC}"
done
```

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

## Comprehensive Testing Strategy

### Multi-Layered Testing Approach

A comprehensive test suite should check multiple aspects of code quality, not just unit tests:

1. **Code Formatting** - Ensure consistent style (black)
2. **Type Safety** - Catch type errors before runtime (mypy)
3. **Importability** - Verify all modules can be imported
4. **Security** - Scan for vulnerabilities (bandit)
5. **Unit Tests** - Test functionality with coverage (pytest)
6. **Coverage Analysis** - Identify untested code paths

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

### Comprehensive Test Script

Create a single `test.sh` script that runs all quality checks:

**Key Features:**
- **Colored output** - Use ANSI colors for better readability (✓/✗ indicators)
- **Progress tracking** - Count tests run vs passed
- **Section headers** - Clear visual separation of test categories
- **Error aggregation** - Track failures across all categories
- **Actionable feedback** - Provide next steps when tests fail

**Example structure:**
```bash
#!/usr/bin/env bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

# Run each test category
# 1. Code formatting
# 2. Type checking
# 3. Import checks
# 4. Security scanning
# 5. Unit tests with coverage
# 6. Final summary
```

### Test Coverage Reporting

**Configure pytest for coverage in `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
addopts = [
    "-v",                              # Verbose output
    "--cov=imessage_analysis",         # Coverage target
    "--cov-report=term-missing",       # Show missing lines in terminal
    "--cov-report=html:htmlcov",       # Generate HTML report
    "--cov-fail-under=30",             # Fail if coverage < 30%
]
```

**Benefits:**
- **Terminal output** - See coverage summary immediately
- **HTML report** - Detailed line-by-line coverage in `htmlcov/index.html`
- **Coverage threshold** - Enforce minimum coverage percentage
- **Missing lines** - See exactly which lines aren't tested

### Security Scanning with Bandit

**Add bandit to dev dependencies:**
```toml
[project.optional-dependencies]
dev = [
    "bandit>=1.7.0",
    # ... other dev deps
]
```

**Run security scans:**
```bash
# Basic scan
bandit -r imessage_analysis

# JSON output for CI
bandit -r imessage_analysis -f json -o bandit_report.json

# Low/medium severity only
bandit -r imessage_analysis -ll
```

**What it catches:**
- SQL injection vulnerabilities
- Hardcoded passwords/secrets
- Insecure random number generation
- Shell injection risks
- Use of dangerous functions

### Pytest Configuration Best Practices

**Test Markers:**
```toml
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

**Usage:**
```bash
# Run only fast tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

**Test Discovery:**
```toml
testpaths = ["tests"]              # Where to find tests
python_files = ["test_*.py"]       # Test file pattern
python_classes = ["Test*"]         # Test class pattern
python_functions = ["test_*"]       # Test function pattern
```

### Import Testing

**Verify all modules can be imported:**
```bash
for module in imessage_analysis imessage_analysis.config \
              imessage_analysis.database; do
  python -c "import $module" || echo "Failed: $module"
done
```

**Why it matters:**
- Catches import errors early
- Verifies package structure
- Ensures dependencies are available
- Prevents runtime import failures

### Test Output and User Experience

**Make test output informative:**

1. **Use colors** - Green for success, red for failure
2. **Show progress** - "Tests Run: X, Passed: Y, Failed: Z"
3. **Section headers** - Clear visual separation
4. **Actionable errors** - Tell users how to fix issues
5. **Summary at end** - Quick overview of all results

**Example:**
```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Running Comprehensive Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  Code Formatting (black)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Code formatting is correct

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Final Test Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tests Run:    7
Tests Passed: 7
Tests Failed: 0

✅ All tests passed!
```

### Running Tests

```bash
# Run comprehensive test suite
./test.sh

# Run only pytest
pytest

# Run with coverage
pytest --cov=imessage_analysis

# Run specific test file
pytest tests/test_queries.py

# Run with markers
pytest -m unit
pytest -m "not slow"
```

### Coverage Thresholds

**Set minimum coverage requirements:**
- Start with a low threshold (e.g., 30%) to establish baseline
- Gradually increase as you add tests
- Use `--cov-fail-under=X` to enforce in CI

**Coverage goals:**
- **30-50%** - Basic coverage, all critical paths tested
- **50-70%** - Good coverage, most functionality tested
- **70-90%** - Excellent coverage, edge cases included
- **90%+** - Comprehensive coverage, all code paths tested

### Test Organization

**Group related tests:**
- One test file per module (e.g., `test_queries.py` for `queries.py`)
- Use descriptive test names: `test_get_latest_messages_includes_limit`
- Test both success and failure cases
- Use fixtures for common setup

**Example:**
```python
def test_get_latest_messages_includes_limit():
    q, params = get_latest_messages(limit=12)
    assert "LIMIT ?" in q
    assert params == (12,)

def test_get_latest_messages_default_limit():
    q, params = get_latest_messages()
    assert params == (10,)  # Default limit
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
11. **Test comprehensively** - format, types, security, coverage, imports
12. **Use colored output** in test scripts for better UX
13. **Set coverage thresholds** to enforce minimum test coverage
14. **Scan for security issues** with bandit in addition to code review
15. **Organize tests by module** - one test file per source module

## ETL & Data Architecture

### Why a Derived Database (analysis.db)?

When working with Apple's iMessage data, you're dealing with **two separate databases**:

1. **chat.db** (Messages) - A hand-designed relational schema, relatively stable
2. **AddressBook-vXX.abcddb** (Contacts) - A Core Data object graph, **not designed for analytics**

Direct cross-database joins are fragile because:
- The Contacts schema changes between macOS versions
- Core Data tables use opaque `Z*` prefixes and unstable primary keys
- You can't safely add indexes or make modifications

**Solution: Create a derived database you own (`analysis.db`)**

This is a **translation boundary** - a local data warehouse that:
- Isolates your analytics from Apple's schema churn
- Provides stable, indexed tables for fast queries
- Supports incremental updates via ETL state tracking
- Allows future migration to DuckDB/Postgres if needed

### Dimensional Modeling Choices

We use dimensional modeling conventions (`dim_*` / `fact_*`):

```
dim_person        - Canonical human identities
dim_contact_method - Normalized phones/emails linked to persons
dim_handle        - Bridges iMessage handles to persons
fact_message      - Main analytical fact table
etl_state         - Tracks sync progress for incremental updates
```

**Why this structure:**
- **Star schema** allows fast analytical queries with minimal joins
- **Dimension tables** (`dim_*`) contain descriptive attributes
- **Fact tables** (`fact_*`) contain measurements (messages)
- **Denormalized person_id in fact_message** - trades storage for query speed

### Phone Normalization Strategy

All phone numbers are normalized to **E.164 format**: `+[country code][number]`

Examples:
- `(415) 555-1234` → `+14155551234`
- `415-555-1234` → `+14155551234`
- `+44 20 7946 0958` → `+442079460958`

**Normalization rules:**
1. Strip all non-digit characters
2. If 10 digits (US), prepend `+1`
3. If 11 digits starting with `1` (US with country code), prepend `+`
4. If already has `+` prefix, preserve country code
5. If ≥7 digits, prepend `+` (best effort)
6. Otherwise, return original (can't normalize)

**Edge cases:**
- Letters in phone numbers (e.g., `1-800-FLOWERS`) - returned as-is if not enough digits
- Very short numbers - returned as-is
- Empty/null values - returned as-is

### Identity Resolution as a Process

Identity resolution is **not a simple JOIN** - it's a multi-step process:

1. **Extract handles** from chat.db with both raw and normalized values
2. **Match handles** against dim_contact_method by normalized value
3. **Create inferred persons** for unmatched handles (source='inferred')
4. **Link handles to persons** in dim_handle.person_id
5. **Denormalize person_id** into fact_message for fast queries

**Why this approach:**
- Separates the matching logic from the data structure
- Supports manual overrides (source='manual')
- Caches resolution results (no re-matching on every query)
- Prepares for future Contacts integration

### Incremental ETL Patterns

**Never rebuild everything.** Use incremental sync via `etl_state`:

```sql
-- Track last synced message date
SELECT value FROM etl_state WHERE key = 'last_message_date';

-- Extract only newer messages
SELECT * FROM message WHERE date > ?;
```

**Incremental strategy:**
1. Check `etl_state.last_message_date`
2. Extract only messages after that date
3. Load new messages (INSERT OR IGNORE)
4. Update `etl_state.last_message_date` with max date
5. Upsert handles (they may change display info)

**Benefits:**
- Fast startup even with large message histories
- Minimal disk I/O for incremental updates
- Idempotent - safe to run multiple times

### SQLite for Local Data Warehousing

SQLite is **good enough** for local analytics:

**When SQLite works:**
- Single user, read-heavy workloads
- Database fits in memory (or SSD is fast enough)
- No concurrent writes needed
- Simple deployment (single file)

**When to upgrade:**
- Need concurrent writes from multiple processes
- Database exceeds available RAM significantly
- Need advanced analytics (window functions with large windows)
- Need columnar storage (consider DuckDB)

**Our approach:**
- Start with SQLite for simplicity
- Design schema to be portable (standard SQL)
- Can migrate to DuckDB or Postgres later if needed

### Validation Checks

After ETL, run automated validation:

| Check | What It Validates |
|-------|-------------------|
| `check_handle_count` | All handles from chat.db exist in dim_handle |
| `check_message_count` | Message counts match (target ≤ source) |
| `check_no_orphan_messages` | All handle_ids reference valid handles |
| `check_normalization_quality` | Phones are E.164 format (≥90%) |
| `check_etl_state` | ETL state contains valid sync timestamps |
| `check_date_formats` | All dates are valid ISO-8601 |

**Usage:**
```python
from imessage_analysis.etl import validate_etl
result = validate_etl(chat_db_path, analysis_db_path)
print(result)  # Shows ✓/✗ for each check
```

### Testing ETL Code

**Test fixtures** create isolated sample databases:

```python
@pytest.fixture
def sample_chat_db(tmp_path) -> Path:
    """Create minimal chat.db with test data."""
    # Creates handles, messages, chats in temp directory

@pytest.fixture
def empty_analysis_db(tmp_path) -> Path:
    """Create empty analysis.db with schema."""
    create_schema(tmp_path / "analysis.db")
```

**Integration tests** use real data when available:

```python
@pytest.mark.integration
def test_real_etl(real_chat_db, tmp_path):
    """Run ETL against real chat.db."""
    # Skipped if ~/Library/Messages/chat.db doesn't exist
```

### Key ETL Takeaways

1. **Treat Apple DBs as unstable external APIs** - read-only, explicit column lists
2. **Create a derived database you own** - stable schema, indexed, query-friendly
3. **Identity resolution is a process** - not a join, cache results
4. **Use incremental sync** - track state, avoid full rebuilds
5. **Validate after ETL** - automated checks catch data quality issues
6. **Test with fixtures and real data** - both synthetic and integration tests
7. **Document design decisions** - in code docstrings and LEARNINGS.md

## Contacts Database (AddressBook) Integration

### Accessing the macOS Contacts Database

Apple's Contacts app stores data in a Core Data database at:
```
~/Library/Application Support/AddressBook/AddressBook-vXX.abcddb
```

**Important constraints:**
- Requires **Full Disk Access** on macOS (Security & Privacy settings)
- Uses Core Data schema with `Z*`-prefixed tables
- Primary keys (`Z_PK`) are **not stable** across syncs
- Schema changes between macOS versions

### Core Data Schema Conventions

The Contacts database uses Core Data conventions:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `ZABCDRECORD` | Contact records | `Z_PK`, `ZFIRSTNAME`, `ZLASTNAME`, `ZORGANIZATION` |
| `ZABCDPHONENUMBER` | Phone numbers | `Z_PK`, `ZOWNER` (→ ZABCDRECORD), `ZFULLNUMBER` |
| `ZABCDEMAILADDRESS` | Email addresses | `Z_PK`, `ZOWNER` (→ ZABCDRECORD), `ZADDRESS` |

**Core Data naming:**
- `Z_PK` - Primary key (integer, auto-incremented)
- `Z*` prefix - Core Data managed columns
- `ZOWNER` - Foreign key to parent record

### Graceful Permission Handling

Since Contacts DB requires Full Disk Access, handle permission denial gracefully:

```python
def _open_contacts_db(path: Path) -> Optional[sqlite3.Connection]:
    """Open AddressBook, returning None if permission denied."""
    try:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        # Test if we can actually query it
        conn.execute("SELECT 1 FROM ZABCDRECORD LIMIT 1")
        return conn
    except sqlite3.OperationalError:
        logger.warning("Cannot access Contacts DB (Full Disk Access required)")
        return None
```

**Key practices:**
- **Test the connection** with a simple query (not just opening)
- **Return None** instead of raising - let the pipeline continue without contacts
- **Log a warning** so users know why contacts weren't synced

### Enhanced Identity Resolution

With contacts data, identity resolution becomes more accurate:

**Resolution strategy (in order):**
1. **Exact match** - Normalized handle matches dim_contact_method.value_normalized
2. **Fuzzy phone match** - Last 10 digits of phone match (handles format variations)
3. **Create inferred person** - No match found, create placeholder

```python
def resolve_handle_to_person(conn, handle_normalized, handle_type):
    # 1. Try exact match
    person_id = exact_match(handle_normalized)
    if person_id:
        return person_id
    
    # 2. Try fuzzy phone match (last 10 digits)
    if handle_type == "phone":
        person_id = fuzzy_phone_match(handle_normalized)
        if person_id:
            return person_id
    
    return None  # Will create inferred person
```

**Why last 10 digits?**
- US phone numbers are 10 digits
- Country codes vary in length (+1, +44, +852)
- Normalizing both sides still may have format variations
- Last 10 digits catches most real-world cases

### Contact Loading Strategy

Contacts are loaded into `dim_person` and `dim_contact_method`:

1. **Extract contacts** from ZABCDRECORD
2. **Generate UUID** for each contact (don't use Z_PK - not stable)
3. **Build display name** from first + last name (or organization)
4. **Set source='contacts'** to distinguish from inferred persons
5. **Load contact methods** (phones/emails) linked to person UUIDs

**Display name priority:**
1. First + Last name ("John Doe")
2. First name only ("John")
3. Last name only ("Doe")
4. Organization ("Apple Inc")
5. Nickname
6. "Unknown Contact"

### Testing with Mock Contacts Database

Create a minimal Contacts DB fixture for testing:

```python
@pytest.fixture
def sample_contacts_db(tmp_path) -> Path:
    """Create minimal AddressBook with Core Data schema."""
    db_path = tmp_path / "AddressBook-v22.abcddb"
    conn = sqlite3.connect(str(db_path))
    
    # Create Core Data schema
    conn.executescript("""
        CREATE TABLE ZABCDRECORD (
            Z_PK INTEGER PRIMARY KEY,
            ZFIRSTNAME TEXT,
            ZLASTNAME TEXT,
            ZORGANIZATION TEXT,
            ZNICKNAME TEXT
        );
        
        CREATE TABLE ZABCDPHONENUMBER (
            Z_PK INTEGER PRIMARY KEY,
            ZOWNER INTEGER,
            ZFULLNUMBER TEXT,
            ZLABEL TEXT
        );
        
        CREATE TABLE ZABCDEMAILADDRESS (
            Z_PK INTEGER PRIMARY KEY,
            ZOWNER INTEGER,
            ZADDRESS TEXT,
            ZLABEL TEXT
        );
    """)
    
    # Insert test data...
    return db_path
```

### Contacts Validation Checks

After ETL with contacts, additional validation:

| Check | What It Validates |
|-------|-------------------|
| `check_contacts_loaded` | dim_person has source='contacts' entries |
| `check_contact_methods_linked` | All contact methods have valid person_id |
| `check_identity_resolution_rate` | % of handles resolved to contacts vs inferred |

**Example output:**
```
✓ Contacts loaded - 156 contacts (45.2% of 345 persons)
✓ Contact methods linked - 289 methods, all linked
✓ Identity resolution rate - 32.5% resolved to contacts (67/206)
```

### Key Contacts Integration Takeaways

1. **Handle permission denial gracefully** - Return None, don't crash
2. **Don't trust Z_PK stability** - Generate your own UUIDs
3. **Use fuzzy phone matching** - Last 10 digits handles format variations
4. **Set source='contacts'** vs 'inferred' - Track provenance
5. **Test with mock databases** - Create fixtures with Core Data schema
6. **Validate contact loading** - Check links and resolution rates
