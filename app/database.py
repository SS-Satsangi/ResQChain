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
            reported_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()