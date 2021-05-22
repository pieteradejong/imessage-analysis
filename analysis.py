import sqlite3
from sqlite3 import Error
import pandas as pd


def create_connection(db_file):
	""" 
	create a database connection
	:param db_file: database file
	:return: Connection object or None
	"""
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)

	return conn

def get_table_names(conn):
	"""
	get all table names
	:param conn: database connection
	:return rows: query result
	"""
	query = "SELECT `name` FROM `sqlite_master` WHERE `type`='table';"
	cur = conn.cursor()
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def get_messages(conn):
	"""
	get messages
	:param conn: database connection
	:return rows: query result
	"""
	query = "SELECT `text` FROM `message` ORDER BY `ROWID` DESC LIMIT 20;"
	cur = conn.cursor()
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def main():
	username = "pdejong"
	db_file = "/Users/" + username + "/Library/Messages/chat.db"
	db_file_alt = "~/Library/Containers/com.apple.iChat/Data/Library/Messages"

	conn = create_connection(db_file)
	with conn:
		print("Table names:")
		table_names = get_table_names(conn)
		print(table_names)

		print("Chat messages")
		messages = get_messages(conn)
		print(messages)

if __name__ == '__main__':
	main()

