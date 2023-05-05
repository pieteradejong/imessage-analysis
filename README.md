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


# Product roadmap

## Uncateogorized todos/ideas
* Add `Attachments` folder analysis
* add __init__.py file to make project a package
* Get date when db last-updated
* TODO add "create" queries to new `.sql` file
* 
## Milestone v0.1: Ability to read table names from `.db` file

* Complete

## Current


## Milestone v0.X: Add UI with visualization

## Milestone v1.0: Self-hosted web app for regular use

# Database structure

## Tables
`deleted_messages`

* table description

`sqlite_sequence`

* table description

`chat_handle_join`

* table description

`sync_deleted_messages`

* table description

`message_processing_task`

* table description

`handle`

* table description

`sync_deleted_chats`

* table description

`message_attachment_join`

* table description

`sync_deleted_attachments`

* table description

`kvtable`

* table description

`chat_message_join`

* table description

`message`

* Arguably the most important table along with `handle` ("contacts" i.e. people). Contains the body of any message sent or received. 

`chat`

* table description

`attachment`

* table description

`sqlite_stat1`

* table description

## How to make this work

* For this script to read your iMessages database file, it needs permission to do so. You can add the relevant application, e.g. Terminal, iTerm, or other, in System Preferences -> Security & Privacy -> Full Disk Access. Do so at your own risk.


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


## Appendix - Brief description of all tables
(For schema details, see `.sql` file on in project root directory.)

`_SqliteDatabaseProperties`
> key
> value
`deleted_messages`
> ROWID
> guid
`sqlite_sequence`
> name
> seq
`chat_handle_join`
> chat_id
> handle_id
`sync_deleted_messages`
> ROWID
> guid
> recordID
`message_processing_task`
> ROWID
> guid
> task_flags
`handle`
> ROWID
> id
> country
> service
> uncanonicalized_id
> person_centric_id
`sync_deleted_chats`
> ROWID
> guid
> recordID
> timestamp
`message_attachment_join`
> message_id
> attachment_id
`sync_deleted_attachments`
> ROWID
> guid
> recordID
`kvtable`
> ROWID
> key
> value
`chat_message_join`
> chat_id
> message_id
> message_date
`message`
> ROWID
> guid
> text
> replace
> service_center
> handle_id
> subject
> country
> attributedBody
> version
> type
> service
> account
> account_guid
> error
> date
> date_read
> date_delivered
> is_delivered
> is_finished
> is_emote
> is_from_me
> is_empty
> is_delayed
> is_auto_reply
> is_prepared
> is_read
> is_system_message
> is_sent
> has_dd_results
> is_service_message
> is_forward
> was_downgraded
> is_archive
> cache_has_attachments
> cache_roomnames
> was_data_detected
> was_deduplicated
> is_audio_message
> is_played
> date_played
> item_type
> other_handle
> group_title
> group_action_type
> share_status
> share_direction
> is_expirable
> expire_state
> message_action_type
> message_source
> associated_message_guid
> associated_message_type
> balloon_bundle_id
> payload_data
> expressive_send_style_id
> associated_message_range_location
> associated_message_range_length
> time_expressive_send_played
> message_summary_info
> ck_sync_state
> ck_record_id
> ck_record_change_tag
> destination_caller_id
> is_corrupt
> reply_to_guid
> sort_id
> is_spam
> has_unseen_mention
> thread_originator_guid
> thread_originator_part
> syndication_ranges
> synced_syndication_ranges
> was_delivered_quietly
> did_notify_recipient
`chat`
> ROWID
> guid
> style
> state
> account_id
> properties
> chat_identifier
> service_name
> room_name
> account_login
> is_archived
> last_addressed_handle
> display_name
> group_id
> is_filtered
> successful_query
> engram_id
> server_change_token
> ck_sync_state
> original_group_id
> last_read_message_timestamp
> cloudkit_record_id
> last_addressed_sim_id
> is_blackholed
> syndication_date
> syndication_type
`attachment`
> ROWID
> guid
> created_date
> start_date
> filename
> uti
> mime_type
> transfer_state
> is_outgoing
> user_info
> transfer_name
> total_bytes
> is_sticker
> sticker_user_info
> attribution_info
> hide_attachment
> ck_sync_state
> ck_server_change_token_blob
> ck_record_id
> original_guid
> is_commsafety_sensitive
`sqlite_stat1`
> tbl
> idx
> stat