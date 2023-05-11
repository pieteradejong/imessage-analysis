# imessage-analysis

# Project prupose and audience

Purpose: enable programmatic analysis my own iMessages, since I find my iPhone and Mac iMessage apps lacking in that area.

Target audience: developers, who know how to "copy your iMessage chat database file, likely `chat.db` into your project folder."

## Requirements

* iMessage data is loaded from the `[chat].db` file stored on your Mac. This may require your Messages app to be configured to sync with between iPhone and Mac. So you need **read-access** to `chat.db`. Write access is not required, and this package makes no changes to this file. Any changes only happen to copies of the file.

### Quick note on local Message files, on Mac
* `[HOME_FOLDER/]Library/Messages/chat.db` - actual chat data.
* `[HOME_FOLDER/]Library/Messages/Attachments` - message attachments
* `[HOME_FOLDER/]Library/Messages/chat.db-shm` - SQLite-specific file, irrelevant to analyis.
* `[HOME_FOLDER/]Library/Messages/chat.db-wal` - "write-ahead log", relevant only operationally, irrelevant to analysis.


## Usage

* Expects database file to be in same directory as `analysis.py`
* For this script to read your iMessages database file, it needs permission to do so. You can add the relevant application, e.g. Terminal, iTerm, or other, in System Preferences -> Security & Privacy -> Full Disk Access. Do so at your own risk.


# Product roadmap

## Uncateogorized todos/ideas
* Add `Attachments` folder analysis
* add __init__.py file to make project a package
* Get date when db last-updated
* TODO add "create" queries to new `.sql` file
* Long term: allow exports of texts or analysis to pdf/spreadsheet
* Database interaction optimizations:
  * rewrite SQL queries to accomplish more within query
  
## Milestone v0.1: Ability to read table names from `.db` file

* Complete

## Current


## Milestone v0.X: Add UI with visualization

## Milestone v1.0: Self-hosted web app for regular use








## Project TODO's
* Separate file for SQL queries
* Function for datetime calculus
* Feature: 
* Adding logging using logging library
* make OOP
* add funciton signature types
* add enriched comments including parameter explanations

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

