import sqlite3
from config import BASE_DIR

DB_PATH = BASE_DIR / "data" / "db.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,

                height REAL NOT NULL CHECK(height > 0),
                start_weight REAL NOT NULL CHECK(start_weight > 0),
                current_weight REAL NOT NULL CHECK(current_weight > 0),
                target_weight REAL NOT NULL CHECK(target_weight > 0),

                next_weight_request_at DATETIME,

                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );


            CREATE TABLE IF NOT EXISTS doses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                medication TEXT NOT NULL,
                dose_value REAL NOT NULL CHECK(dose_value > 0),
                price REAL NOT NULL CHECK(price >= 0),

                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),

                UNIQUE(medication, dose_value)
            );


            CREATE TABLE IF NOT EXISTS user_doses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                dose_id INTEGER NOT NULL,

                start_date DATE NOT NULL,
                end_date DATE,

                start_weight REAL CHECK(start_weight > 0),
                end_weight REAL CHECK(end_weight > 0),

                status TEXT NOT NULL DEFAULT 'planned'
                    CHECK(status IN (
                        'planned',
                        'active',
                        'completed',
                        'cancelled'
                    )),

                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (dose_id)
                    REFERENCES doses(id)
                    ON DELETE RESTRICT
            );


            CREATE TABLE IF NOT EXISTS weight_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                weight REAL NOT NULL CHECK(weight > 0),

                recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );


            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                dose_id INTEGER NOT NULL,

                user_phone TEXT NOT NULL,

                weeks_count INTEGER NOT NULL CHECK(weeks_count > 0),

                discount INTEGER NOT NULL DEFAULT 0
                    CHECK(discount BETWEEN 0 AND 100),

                total_price REAL NOT NULL CHECK(total_price >= 0),

                delivery_data TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'new'
                    CHECK(status IN (
                        'new',
                        'processed',
                        'completed'
                    )),

                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE RESTRICT,

                FOREIGN KEY (dose_id)
                    REFERENCES doses(id)
                    ON DELETE RESTRICT
            );


            CREATE INDEX IF NOT EXISTS idx_user_doses_user_id
                ON user_doses(user_id);


            CREATE INDEX IF NOT EXISTS idx_user_doses_status
                ON user_doses(status);


            CREATE INDEX IF NOT EXISTS idx_weight_history_user_id
                ON weight_history(user_id);


            CREATE INDEX IF NOT EXISTS idx_orders_user_id
                ON orders(user_id);


            CREATE INDEX IF NOT EXISTS idx_orders_status
                ON orders(status);
            """
        )

        connection.commit()

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")