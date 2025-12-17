# Migration Guide

This document explains the new project structure and how to migrate from the old structure.

## New Structure

The project has been reorganized into a proper Python package structure:

```
imessage-analysis/
├── imessage_analysis/          # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── database.py             # Database connection and queries
│   ├── queries.py              # SQL query definitions
│   ├── analysis.py             # High-level analysis functions
│   ├── visualization.py        # Plotting and visualization
│   ├── utils.py                # Utility functions
│   └── logger_config.py        # Logging configuration
├── main.py                     # New main entry point
├── config.py                   # Root-level config (for backward compatibility)
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
├── pyproject.toml              # Modern Python project config
└── [old files]                 # Legacy files (see below)
```

## Key Changes

### 1. Package Structure
- Code is now organized in the `imessage_analysis` package
- Proper `__init__.py` files for package imports
- Clear separation of concerns (database, queries, analysis, visualization)

### 2. Configuration
- New `Config` class in `imessage_analysis.config`
- Automatically finds `chat.db` in current directory or default Messages location
- Can be configured programmatically or via command line

### 3. Database Access
- New `DatabaseConnection` class with context manager support
- Better error handling and logging
- Read-only access by default

### 4. Logging
- Replaced print statements with proper logging
- Configurable log levels and output

### 5. Dependencies
- `requirements.txt` for pip installation
- `setup.py` and `pyproject.toml` for package installation

## Migration Steps

### For Script Usage

**Old way:**
```python
import sqlite3
from queries import table_names
# ...
```

**New way:**
```python
from imessage_analysis import get_config, DatabaseConnection
from imessage_analysis.analysis import get_database_summary

config = get_config()
with DatabaseConnection(config) as db:
    summary = get_database_summary(db)
```

### For Command Line Usage

**Old way:**
```bash
python analysis.py
```

**New way:**
```bash
python main.py
# Or after installation:
imessage-analysis
```

## Legacy Files

The following files are kept for backward compatibility but are deprecated:
- `analysis.py` - Use `main.py` and `imessage_analysis/analysis.py` instead
- `queries.py` - Use `imessage_analysis/queries.py` instead
- `util.py` - Use `imessage_analysis/utils.py` instead
- `viz.py` - Use `imessage_analysis/visualization.py` instead

These will be removed in a future version.

## Installation

### Development Installation
```bash
pip install -e .
```

### Production Installation
```bash
pip install -r requirements.txt
```

## Benefits of New Structure

1. **Better Organization**: Clear module separation
2. **Reusability**: Can be imported as a package
3. **Maintainability**: Easier to test and extend
4. **Professional**: Follows Python packaging best practices
5. **Type Safety**: Better type hints throughout
6. **Error Handling**: Proper exception handling
7. **Logging**: Structured logging instead of print statements


