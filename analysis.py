import sqlite3
from sqlite3 import Error
from util import bcolors
import os 

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
	cur = conn.cursor()
	query = "SELECT `name` FROM `sqlite_master` WHERE `type`='table';"
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def get_columns_for_table(conn, table_name):
	cur = conn.cursor()
	cur = conn.execute("select * from " + table_name + ";")

	return cur.description


def get_messages(conn):
	"""
	get messages
	:param conn: database connection
	:return rows: query result
	"""
	cur = conn.cursor
	query = "SELECT `text` FROM `message` ORDER BY `ROWID` DESC LIMIT 20;"
	cur.execute(query)

	rows = cur.fetchall()

	return rows

def get_contacts_created_in_timeframe(conn, start, end):
	pass

def main():
	conn = None
	try:
		dir_path = os.path.dirname(os.path.realpath(__file__))
		db_file_name = "chat.db"
		conn = sqlite3.connect(f"file:{dir_path}/{db_file_name}?mode=ro", uri=True)
	except sqlite3.Error as err:
		print(f"{bcolors.FAIL}sqlite3 Error: {err}{bcolors.ENDC}")

	tables = get_table_names(conn)
	for name in tables:
		print("`" + name[0] + "`")
		# cols = get_columns_for_table(conn, name[0])
		# for c in cols:
		# 	print("> " + c[0])

	return conn

if __name__ == '__main__':	
	main()
