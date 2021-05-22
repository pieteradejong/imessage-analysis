import sqlite3
import pandas as pd

username = ""
messages_location = "/Users/" + username + "/Library/Messages/chat.db"
messages_location_alt = "~/Library/Containers/com.apple.iChat/Data/Library/Messages"

conn = sqlite3.connect()

get_table_names(conn)
get_messages(conn)

def get_table_names(conn):
	"""
	get all table names
	"""
	query = "SELECT name FROM sqlite_master WHERE type='table';";
	cur = conn.cursor()
    cur.execute(query)

    rows = cur.fetchall()

    return rows

def get_messages(conn):
	"""
	get messages
	"""
	query = "SELECT text FROM message ORDER BY ROWID DESC LIMIT 20;"
	cur = conn.cursor()
    cur.execute(query)

    rows = cur.fetchall()

    return rows
