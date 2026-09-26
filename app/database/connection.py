import sqlite3
from pathlib import Path
from config import DB_PATH

def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection