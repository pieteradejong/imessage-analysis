# Database

Interacting with a sqlite3 database e.g. `chat.db` using the prompt:

Open database:
`$ sqlite3 chat.db`

Show schema (`CREATE_TABLE`, `CREATE_INDEX`, `CREATE_TRIGGER`, etc.) command for a table:
`sqlite> .schema <table_name>`

Show schema for entire databse:
`sqlite> .schema`

Getting schema for a table by querying the database:

`SELECT sql FROM sqlite_master WHERE tbl_name = 'message';`
