# iMessage Analysis

# Project prupose and audience

Purpose: enable programmatic analysis my own iMessages, since I find my iPhone and Mac iMessage apps lacking in that area.

Target audience: developers, who know how to "copy your iMessage chat database file, likely `chat.db` into your project folder."

## Usage / Requirements

* Expects database file to be in same directory as `analysis.py`
* For this script to read your iMessages database file, it needs permission to do so. You can add the relevant application, e.g. Terminal, iTerm, or other, in System Preferences -> Security & Privacy -> Full Disk Access. Do so at your own risk.
* iMessage data is loaded from the `[chat].db` file stored on your Mac. This may require your Messages app to be configured to sync with between iPhone and Mac. So you need **read-access** to `chat.db`. Write access is not required, and this package makes no changes to this file. Any changes only happen to copies of the file.

### Quick note on local Message files, on Mac
* `[HOME_FOLDER/]Library/Messages/chat.db` - actual chat data.
* `[HOME_FOLDER/]Library/Messages/Attachments` - message attachments
* `[HOME_FOLDER/]Library/Messages/chat.db-shm` - SQLite-specific file, irrelevant to analyis.
* `[HOME_FOLDER/]Library/Messages/chat.db-wal` - "write-ahead log", relevant only operationally, irrelevant to analysis.

# Product roadmap

## Milestone v0.1: Databse equivalent of Hello World
* :white_check_mark: connect to `chat.db`
* :white_check_mark: read table stats e.g. tables, rows, row counts

## Uncategorized todos/ideas
* add `Attachments` folder analysis
* if possible, get date when overall db last-updated
* rewrite SQL queries to accomplish more within query
* (medium priority) use `logging`
* (low priority) allow exports of texts or analysis to `.pdf`/spreadsheet
## Project Organization
* :white_check_mark: Separate file for SQL queries
* :todo: add "create" queries to new `.sql` file
## Project Design
* OOP versus functions
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

