from app.database.connect import get_connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    height REAL NOT NULL,
    start_weight REAL NOT NULL,
    current_weight REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doses  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dose_value REAL NOT NULL,
    medication TEXT NOT NULL,
    price REAL NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    dose_id INTEGER NOT NULL,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP DEFAULT NULL,
    status TEXT NOT NULL,
        
    FOREIGN KEY (user_id) 
        REFERENCES users (id),
        
    FOREIGN KEY (dose_id) 
        REFERENCES doses (id)
        
    )""")

    connection.commit()
    connection.close()

