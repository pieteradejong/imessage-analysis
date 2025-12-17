# iMessage Analysis

# Purpose and audience

Enable programmatic analysis and visualization of iMessages which are commonly used on Apple devices. 
Examples of use cases:
* how many people have you corresponded with in the last month or year?
* who is the quickest, or slowest, to text back?
* who have you messaged with most during a particular time? 
* have you lost touch with anyone?

Target audience: any iMessage user, current or past. Project requires direct `read` access to the relevant database file, so currently requires minor technical skills.

## Installation

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd imessage-analysis

# Install dependencies
pip install -r requirements.txt

# Or install as a package (recommended)
pip install -e .
```

### Requirements
* Python 3.12
* macOS (for accessing the Messages database)
* Read access to `chat.db` file

## Usage

### Command Line
```bash
# Run the main analysis script
python main.py

# Or if installed as package
imessage-analysis
```

The script will automatically look for `chat.db` in:
1. Current directory
2. Default Messages location: `~/Library/Messages/chat.db`

### Programmatic Usage
```python
from imessage_analysis import get_config, DatabaseConnection
from imessage_analysis.analysis import get_database_summary, get_latest_messages_data

# Get configuration (auto-detects database location)
config = get_config()

# Or specify custom path
config = get_config(db_path="/path/to/chat.db")

# Use database connection
with DatabaseConnection(config) as db:
    # Get database summary
    summary = get_database_summary(db)
    print(f"Total messages: {summary['total_messages']}")
    
    # Get latest messages
    messages = get_latest_messages_data(db, limit=10)
    for msg in messages:
        print(f"{msg['date']}: {msg['text']}")
```

### Requirements

* All relevant iMessage personal data is stored in `chat.db`. The project requires `read` access to this file.
* The database location is now configurable (see `config.py` or use `get_config()`).
* For this file to contain up-to-date data, you must have sync enabled between your iPhone and your Mac laptop/computer.

### Quick note on local Message files, on Mac
* `[HOME_FOLDER/]Library/Messages/chat.db` - actual chat data.
* `[HOME_FOLDER/]Library/Messages/Attachments` - message attachments
* `[HOME_FOLDER/]Library/Messages/chat.db-shm` - SQLite-specific file, irrelevant to analyis.
* `[HOME_FOLDER/]Library/Messages/chat.db-wal` - "write-ahead log", relevant only operationally, irrelevant to analysis.

# Product roadmap

## Milestone v0.1: Database equivalent of Hello World
* :white_check_mark: connect to `chat.db`
* :white_check_mark: read table stats e.g. tables, rows, row counts
* :white_check_mark: read 10 latest messages
* :white_check_mark: proper package structure
* :white_check_mark: configuration management
* :white_check_mark: logging system
* &#9744; if possible, get date when overall db last-updated

## Project Structure

The project is organized as a proper Python package:

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
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
└── pyproject.toml              # Modern Python project config
```

## Uncategorized todos/ideas
* add `Attachments` folder analysis
* if possible, get date when overall db last-updated
* rewrite SQL queries to accomplish more within query
* (low priority) allow exports of texts or analysis to `.pdf`/spreadsheet
* Add unit tests
* Add type checking with mypy
* Add code formatting with black

## Project Organization
* :white_check_mark: Separate file for SQL queries
* :white_check_mark: add "`TABLE CREATE`" queries for each table to new `.sql` file
* :white_check_mark: make `chat.db` file location configurable (`config.py`)
* :white_check_mark: proper package structure with `__init__.py`
* :white_check_mark: use `logging` instead of print statements

## Project Design
* :white_check_mark: OOP for database connections (DatabaseConnection class)
* :white_check_mark: Functions for analysis operations
* :white_check_mark: Consistent type annotations throughout
* :white_check_mark: Package structure with `__init__.py` files
  
## Documentation
* :white_check_mark: Docstrings added to all functions (Google style)
* :pencil: Consider autogenerating docs with Sphinx

### User Interface / Visualization
## Milestone v1.0: Self-hosted web app for personal use
## Milestone: vPublic, productize for public use


### Interesting metrics:
* Percentage breakdown of you-versus-other(s) message count per chat(group)
* per chat between you and another (and aggregate up to overall), mean/median/skew on both message length and frequency
** for all your 1-1 chats, plot 2D frequency and length of overall messages
* your most actively messages sent during 24hrs

## Appendix - Useful resources and links

I used the following for inspiration:
https://stmorse.github.io/journal/iMessage.html
* Analysis and query ideas.
https://spin.atomicobject.com/2020/05/22/search-imessage-sql/
* Analysis and query ideas.
https://linuxsleuthing.blogspot.com/2015/01/getting-attached-apple-messaging.html
* Description of figuring out Message attachments. And the inspiration to add full `CREATE TABLE` `.sql` file to the repo(a TODO as of this writing).
https://github.com/dsouzarc/iMessageAnalyzer
* Existing but older analysis app for Mac. Used for feature and visualization ideas.
