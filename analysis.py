import sqlite3
from sqlite3 import Error
from util import bcolors
import os 
import queries

DB_FILE_NAME = "chat.db"

def create_connection(db_file: str) -> sqlite3.Connection:
	"""Creates a database connection from file."""
	conn = None
	try:
		conn = sqlite3.connect(db_file)
	except Error as e:
		print(e)

	return conn

def get_table_names(conn: sqlite3.Connection) -> list:
	"""Returns all table names in database."""
	cur = conn.cursor()
	query = queries.table_names()
	cur.execute(query)

	table_names = cur.fetchall()

	return table_names

def get_columns_for_table(conn: sqlite3.Connection, table_name: str) -> list:
	cur = conn.cursor()
	# TODO: add warning (and verify) that `pragma_table_info` and other pragma functions
	# are only available in sqlite3 versions >=3.16.0
	query = queries.columns_for_table_q(table_name)
	cur = conn.execute(query)

	return cur.fetchall()

def get_table_creation_query(conn: sqlite3.Connection, table_name: str) -> list:
	cur = conn.cursor()
	query = queries.table_creation_query(table_name)
	cur = conn.execute(query)

	return cur.fetchall()

def main():
	conn = None
	try:
		dir_path = os.path.dirname(os.path.realpath(__file__))
		conn = sqlite3.connect(f"file:{dir_path}/{DB_FILE_NAME}?mode=ro", uri=True)
	except sqlite3.Error as err:
		print(f"{bcolors.FAIL}sqlite3 Error: {err}{bcolors.ENDC}")

	table_names = get_table_names(conn)
	print(f"Table names:\n")
	for tn in table_names:
		print("\t`" + tn[0] + "`")
		
	print(f"All column names in `message` table:\n")
	col_list = get_columns_for_table(conn, 'message')
	print(col_list)
	creation_query = get_table_creation_query(conn, 'attachment')
	print(f"Creation query for attachments table:\n")
	print(creation_query)
	return conn

if __name__ == '__main__':	
	main()
