import sqlite3
import pandas as pd

# substitute username with your username
username = ""
conn = sqlite3.connect("/Users/" + username + "/Library/Messages/chat.db")
# ~/Library/Containers/com.apple.iChat/Data/Library/Messages

# get the names of the tables in the database

cursor = conn.cursor()

# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
cursor.execute("SELECT text FROM message ORDER BY ROWID DESC LIMIT 20;")

for table in cursor.fetchall():
    print(table)

# messages = pd.read_sql_query("select * from message order by rowid desc limit 10", conn)
# print(messages)



