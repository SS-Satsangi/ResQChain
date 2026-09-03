import sqlite3

DATABASE = "resqchain.db"

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS disasters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL,
            reported_at TEXT
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(disasters)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "reported_at" not in column_names:
        connection.execute(
            "ALTER TABLE disasters ADD COLUMN reported_at TEXT"
        )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()