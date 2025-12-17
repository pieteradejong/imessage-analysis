from contextlib import closing
import sqlite3
from sqlite3 import Error
from util import bcolors
import queries

# with closing(sqlite3.connect("aquarium.db")) as connection:
#     with closing(connection.cursor()) as cursor:
#         rows = cursor.execute("SELECT 1").fetchall()
#         print(rows)


DB_FILE_NAME = "chat.db"


def create_connection(db_file: str) -> sqlite3.Connection:
    """Creates a database connection from file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


# (BEGIN) Database metadata functions


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


def get_row_counts_by_table(conn: sqlite3.Connection, table_names: list) -> list:
    cur = conn.cursor()
    query = queries.rows_count(table_names)
    cur.execute(query)
    row_counts = cur.fetchall()[0]
    # print(f"zip 1: {row_counts}\n\n")
    # print(f"zip 2: {table_names}\n\n")

    return list(zip(table_names, row_counts))


def get_table_creation_query(conn: sqlite3.Connection, table_name: str) -> list:
    cur = conn.cursor()
    query = queries.table_creation_query(table_name)
    # table_creation_query now returns a parameterized query
    cur.execute(query, (table_name,))

    return cur.fetchall()


# (END) Database metadata functions

# (BEGIN) User data functions


def get_all_contacts(conn: sqlite3.Connection) -> list:
    cur = conn.cursor()
    query = queries.get_all_contacts()
    cur = conn.execute(query)

    return cur.fetchall()


# (END) User data functions


# TODO NEXT STEP: wrap all queries in "as cursor"
def main2():
    with closing(sqlite3.connect(f"file:{DB_FILE_NAME}?mode=ro", uri=True)) as conn:
        with closing(conn.cursor()) as cursor:
            table_names = get_table_names(conn)
        print(f"Table names:\n")
        for tn in table_names:
            print("\t`" + tn[0] + "`")

        print(f"All column names in `message` table:\n")
        col_list = get_columns_for_table(conn, "message")
        print(col_list)
        creation_query = get_table_creation_query(conn, "attachment")
        print(f"Creation query for attachments table:\n")
        print(creation_query)


def main():
    conn = None
    try:
        conn = sqlite3.connect(f"file:{DB_FILE_NAME}?mode=ro", uri=True)
    except sqlite3.Error as err:
        print(f"{bcolors.FAIL}sqlite3 Error: {err}{bcolors.ENDC}")

    ## Database report

    # Table names
    table_names: list[tuple] = get_table_names(conn)
    table_names: list[str] = list(map(lambda x: x[0], table_names))
    print("Table names:\n")
    print(*table_names, sep="\n")

    # Row counts by table
    print(f"\nRow counts by table:\n")
    row_counts_by_table = get_row_counts_by_table(conn, table_names)
    print(*row_counts_by_table, sep="\n")

    print(f"\n\nAll column names in `message` table:\n")
    col_list = get_columns_for_table(conn, "message")
    print(col_list)

    print(f"Creation query for `attachments` table:\n")
    creation_query = get_table_creation_query(conn, "attachment")
    print(creation_query)


if __name__ == "__main__":
    main()
