from app.database.connect import get_connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    height REAL NOT NULL,
    start_weight REAL NOT NULL,
    current_weight REAL NOT NULL,
    target_weight REAL NOT NULL,
    next_weight_request_at DATE,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doses  (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication TEXT NOT NULL,
    dose_value REAL NOT NULL,
    price REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    dose_id INTEGER NOT NULL,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE DEFAULT NULL,
    start_weight REAL NOT NULL,
    end_weight REAL DEFAULT  NULL,
    status TEXT NOT NULL,
        
    FOREIGN KEY (tg_id) 
        REFERENCES users (tg_id),
        
    FOREIGN KEY (dose_id) 
        REFERENCES doses (id)
        
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    recorded_at DATE NOT NULL DEFAULT CURRENT_DATE
    )""")


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    user_phone TEXT NOT NULL,
    dose_id INTEGER NOT NULL,
    weeks_count INTEGER NOT NULL,
    discount INTEGER NOT NULL,
    total_price REAL NOT NULL,
    delivery_data TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
    )""")

    connection.commit()
    connection.close()

if __name__ == "__main__":
    init_db()

