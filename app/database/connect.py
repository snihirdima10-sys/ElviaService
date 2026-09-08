import sqlite3

def get_connection():
    connection = sqlite3.connect("db.db")\

    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection