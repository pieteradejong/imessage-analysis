# Table descriptions

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