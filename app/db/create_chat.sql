CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT, guid TEXT UNIQUE NOT NULL, style INTEGER, state INTEGER, account_id TEXT, properties BLOB, chat_identifier TEXT, service_name TEXT, room_name TEXT, account_login TEXT, is_archived INTEGER DEFAULT 0, last_addressed_handle TEXT, display_name TEXT, group_id TEXT, is_filtered INTEGER DEFAULT 0, successful_query INTEGER, engram_id TEXT, server_change_token TEXT, ck_sync_state INTEGER DEFAULT 0, original_group_id TEXT, last_read_message_timestamp INTEGER DEFAULT 0, cloudkit_record_id TEXT, last_addressed_sim_id TEXT, is_blackholed INTEGER DEFAULT 0, syndication_date INTEGER DEFAULT 0, syndication_type INTEGER DEFAULT 0, is_recovered INTEGER DEFAULT 0);
CREATE INDEX chat_idx_chat_identifier_service_name ON chat(chat_identifier, service_name);
CREATE INDEX chat_idx_chat_identifier ON chat(chat_identifier);
CREATE INDEX chat_idx_chat_room_name_service_name ON chat(room_name, service_name);
CREATE INDEX chat_idx_is_archived ON chat(is_archived);
CREATE INDEX chat_idx_group_id ON chat(group_id);
CREATE TRIGGER after_delete_on_chat AFTER DELETE ON chat BEGIN DELETE FROM chat_message_join WHERE chat_id = OLD.ROWID; END;