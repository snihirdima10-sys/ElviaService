import sqlite3
from pathlib import Path

def get_connection():
    DB_PATH = Path(__file__).resolve().parent.parent.parent / "db.db"
    connection = sqlite3.connect(DB_PATH)

    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection