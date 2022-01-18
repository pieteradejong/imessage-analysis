import sqlite3
from sqlite3 import Error
# import pandas as pd


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

def get_table_names(cur):
	"""
	get all table names
	:param conn: database connection
	:return rows: query result
	"""
	query = "SELECT `name` FROM `sqlite_master` WHERE `type`='table';"
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def get_columns_for_table(conn, table_name):
	cur = conn.execute("select * from " + table_name + ";")

	return cur.description


def get_messages(cur):
	"""
	get messages
	:param conn: database connection
	:return rows: query result
	"""
	query = "SELECT `text` FROM `message` ORDER BY `ROWID` DESC LIMIT 20;"
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def get_contacts_created_in_timeframe(cur, start, end):
	# query = " SELECT  "
	pass


# def get_last_msgs_for_

def main():
	db_file = "/Users/pieterdejong/Library/Messages/chat.db"
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)

	cur = conn.cursor()

	tables = get_table_names(cur)
	for name in tables:
		print("`" + name[0] + "`")
		cols = get_columns_for_table(conn, name[0])
		for c in cols:
			print("> " + c[0])

	

	return conn


if __name__ == '__main__':
	main()
