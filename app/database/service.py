from app.database.connection import get_connection
import sqlite3


def get_user_by_id(tg_id : int) -> dict | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    connection.close()
    return dict(user) if user is not None else None

def find_users(search: str) -> list[dict]:
    connection = get_connection()
    cursor = connection.cursor()

    search = search.strip()

    if search.replace("+", "").replace(" ", "").isdigit():
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE phone LIKE ?
            LIMIT 20
            """,
            (f"%{search}%",)
        )

    else:
        words = search.split()

        conditions = []
        params = []

        for word in words:
            conditions.append("LOWER(full_name) LIKE LOWER(?)")
            params.append(f"%{word}%")

        query = f"""
            SELECT *
            FROM users
            WHERE {" AND ".join(conditions)}
            LIMIT 20
        """

        cursor.execute(query, params)

    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_active_dose_by_user_id(tg_id: int) -> dict | None:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT 
        doses.medication, 
        doses.dose_value, 
        user_doses.start_date,
        doses.price,
        doses.id
    FROM user_doses 
    JOIN doses ON doses.id = user_doses.dose_id
    WHERE tg_id = ? AND status = 'active'""", (tg_id,))

    dose = cursor.fetchone()
    connection.close()
    return dict(dose) if dose is not None else None


def get_first_therapy_date(tg_id: int) -> str | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT MIN(start_date)
        FROM user_doses
        WHERE tg_id = ?
    """, (tg_id,))

    first_date = cursor.fetchone()[0]

    connection.close()
    return first_date

def get_doses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM doses""")
    doses = cursor.fetchall()

    cursor.close()
    return [dict(dose) for dose in doses] if doses else None

def get_dose_by_id(dose_id: int) -> dict | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""SELECT * FROM doses WHERE id = ?""", (dose_id,))
    dose = cursor.fetchone()
    cursor.close()
    return dict(dose) if dose is not None else None

def get_user_orders(tg_id: int) -> list | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            orders.*,
            doses.medication,
            doses.dose_value
        FROM orders
        JOIN doses ON doses.id = orders.dose_id
        WHERE tg_id = ?
        """, (tg_id,))

    orders = cursor.fetchall()

    cursor.close()
    return [dict(order) for order in orders] if orders else None

def create_user(
    tg_id,
    full_name,
    phone,
    height,
    start_weight,
    current_weight,
    target_weight,
    next_weight_request_at
):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (
                tg_id,
                full_name,
                phone,
                height,
                start_weight,
                current_weight,
                target_weight,
                next_weight_request_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tg_id,
            full_name,
            phone,
            height,
            start_weight,
            current_weight,
            target_weight,
            next_weight_request_at
        ))

        connection.commit()
        return True
    except sqlite3.Error as error:
        print(f"Помилка додавання користувача: {error}")
        return False

    finally:
        cursor.close()



def get_user_dose_history(tg_id: int) -> list | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT 
        user_doses.*,
        doses.medication,
        doses.dose_value
    FROM user_doses 
    JOIN doses 
        ON doses.id = user_doses.dose_id
    WHERE tg_id = ? AND status = 'completed'
    
    """, (tg_id,))
    doses = cursor.fetchall()
    cursor.close()
    return [dict(dose) for dose in doses] if doses else None

def get_order(order_id: int) -> dict | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            orders.*,
            doses.medication,
            doses.dose_value,
            users.full_name
        FROM orders
        JOIN doses 
            ON orders.dose_id = doses.id
        JOIN users 
            ON orders.tg_id = users.tg_id
        WHERE orders.id = ?""", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    return dict(order) if order is not None else None

def update_order_status(order_id: int, status: str) -> bool:
    ALLOWED_ORDER_STATUSES = {"new", "processed", "completed"}
    if status not in ALLOWED_ORDER_STATUSES:
        raise ValueError("Invalid order status")
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )

        connection.commit()
        return cursor.rowcount > 0

    except sqlite3.Error:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_orders_by_status(status: str) -> list[dict]:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 
            orders.*,
            users.full_name 
        FROM orders
        JOIN users 
            ON users.tg_id = orders.tg_id 
        WHERE status = ?""",
        (status,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]

def update_weight(tg_id: int, new_weight: float) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO weight_history (tg_id, weight)
        VALUES (?, ?)
    """, (tg_id, new_weight))

    cursor.execute(
        """
            UPDATE users
            SET current_weight = ?
            WHERE tg_id = ?
        """, (new_weight, tg_id)
    )

    connection.commit()
    connection.close()


def create_order(tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status = "NEW"):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO orders (
                tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status))
    except sqlite3.Error:
        connection.close()
        return False

    connection.commit()
    connection.close()
    return True
