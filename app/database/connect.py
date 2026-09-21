import sqlite3
from pathlib import Path

def get_connection():
    BASE_DIR = Path(__file__).resolve().parents[2]
    DB_PATH = BASE_DIR / "data" / "db.db"
    connection = sqlite3.connect(DB_PATH)

    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection