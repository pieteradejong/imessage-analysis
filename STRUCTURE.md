# Project Structure Guide

This document explains the improved project structure and architectural decisions.

## Directory Structure

```
imessage-analysis/
├── imessage_analysis/          # Main Python package
│   ├── __init__.py            # Package initialization and exports
│   ├── config.py              # Configuration management
│   ├── database.py             # Database connection and operations
│   ├── queries.py              # SQL query string definitions
│   ├── analysis.py             # High-level analysis functions
│   ├── visualization.py       # Plotting and visualization
│   ├── utils.py                # Utility functions and classes
│   └── logger_config.py        # Logging setup
├── app/                        # Legacy app directory (database schemas)
│   ├── db/                     # SQL schema files
│   └── utils/                  # Legacy utilities
├── main.py                     # Main entry point (CLI)
├── config.py                   # Root-level config (backward compat)
├── requirements.txt            # Python dependencies
├── setup.py                    # Package installation config
├── pyproject.toml              # Modern Python project metadata
├── README.md                   # Project documentation
├── MIGRATION.md                # Migration guide from old structure
└── STRUCTURE.md                # This file
```

## Module Responsibilities

### `imessage_analysis/__init__.py`
- Package initialization
- Exports main public API
- Version information

### `imessage_analysis/config.py`
- Configuration management
- Database path detection and validation
- Global configuration instance

### `imessage_analysis/database.py`
- Database connection management
- Context manager support
- Read-only access enforcement
- Database metadata queries
- Low-level database operations

### `imessage_analysis/queries.py`
- SQL query string definitions
- Query builders
- Reusable query templates

### `imessage_analysis/analysis.py`
- High-level analysis functions
- Data aggregation and statistics
- Business logic for message analysis

### `imessage_analysis/visualization.py`
- Plotting functions using plotly
- Chart generation
- Data visualization

### `imessage_analysis/utils.py`
- Utility functions
- Helper classes (e.g., Colors)
- Formatting utilities

### `imessage_analysis/logger_config.py`
- Logging configuration
- Log level management
- Output formatting

### `main.py`
- Command-line interface
- Entry point for CLI usage
- User-facing output formatting

## Design Principles

### 1. Separation of Concerns
- **Database layer**: `database.py` handles all database operations
- **Query layer**: `queries.py` contains SQL strings
- **Business logic**: `analysis.py` contains analysis functions
- **Presentation**: `visualization.py` and `main.py` handle output

### 2. Configuration Management
- Centralized configuration in `config.py`
- Automatic path detection
- Validation before use
- Global instance pattern for easy access

### 3. Error Handling
- Proper exception handling throughout
- Meaningful error messages
- Logging for debugging

### 4. Type Safety
- Type hints on all functions
- Optional types for nullable values
- Return type annotations

### 5. Logging
- Structured logging instead of print statements
- Configurable log levels
- Both console and file output support

### 6. Context Managers
- Database connections use context managers
- Automatic resource cleanup
- Exception-safe operations

## Usage Patterns

### Basic Usage
```python
from imessage_analysis import get_config, DatabaseConnection
from imessage_analysis.analysis import get_database_summary

config = get_config()
with DatabaseConnection(config) as db:
    summary = get_database_summary(db)
```

### Custom Configuration
```python
from imessage_analysis.config import Config

config = Config(db_path="/custom/path/to/chat.db")
with DatabaseConnection(config) as db:
    # Use database
    pass
```

### Direct Query Execution
```python
from imessage_analysis import get_config, DatabaseConnection
from imessage_analysis.queries import get_latest_messages

config = get_config()
with DatabaseConnection(config) as db:
    query, params = get_latest_messages(limit=20)
    results = db.execute_query(query, params)
```

## Benefits of This Structure

1. **Maintainability**: Clear module boundaries and responsibilities
2. **Testability**: Each module can be tested independently
3. **Reusability**: Functions can be imported and used in other projects
4. **Scalability**: Easy to add new features without breaking existing code
5. **Professional**: Follows Python packaging best practices
6. **Documentation**: Clear structure makes it easier to document

## Future Improvements

1. **Testing**: Add unit tests for each module
2. **Type Checking**: Add mypy configuration and type stubs
3. **Code Formatting**: Add black configuration
4. **Documentation**: Generate API docs with Sphinx
5. **CLI**: Add argparse for command-line options
6. **Configuration**: Support environment variables and config files


