# iMessage Analysis

# Purpose and audience

Enable programmatic analysis of iMessages which are commonly used on Apple devices.

Target audience: any iMessage user, current or past. Project requires direct `read` access to the relevant database file, so currently requires minor technical skills.

## Usage / Requirements

* All relevant iMessage personal data is stored in `chat.db`. The project requires `read` access to this file, and for now, it must be in the same directory as `analysis.py`. For now, this must be done manually.
* Further, for this file to contain up-to-date data, you must have sync enabled between your iPhone and your Mac laptop/computer.

### Quick note on local Message files, on Mac
* `[HOME_FOLDER/]Library/Messages/chat.db` - actual chat data.
* `[HOME_FOLDER/]Library/Messages/Attachments` - message attachments
* `[HOME_FOLDER/]Library/Messages/chat.db-shm` - SQLite-specific file, irrelevant to analyis.
* `[HOME_FOLDER/]Library/Messages/chat.db-wal` - "write-ahead log", relevant only operationally, irrelevant to analysis.

# Product roadmap

## Milestone v0.1: Databse equivalent of Hello World
* :white_check_mark: connect to `chat.db`
* :white_check_mark: read table stats e.g. tables, rows, row counts
* :clock8: read 10 latest messages
* &#9744; if possible, get date when overall db last-updated

## Uncategorized todos/ideas
* add `Attachments` folder analysis
* if possible, get date when overall db last-updated
* rewrite SQL queries to accomplish more within query
* (medium priority) use `logging`
* (low priority) allow exports of texts or analysis to `.pdf`/spreadsheet

## Project Organization
* :white_check_mark: Separate file for SQL queries
* :pencil: add "`TABLE CREATE`" queries for each table to new `.sql` file
* :pencil: make `chat.db` file location configurable (`config.py`)

## Project Design
* OOP versus functions. Which is suited where.
* Typing: consistent type annotations. Where do annotations make sense and where not.
* Add __init__.py file to make project a package?
  
## Documentation
* Add docstrings for each function? Which convention to follow. Potentially autogenerate docs.

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
