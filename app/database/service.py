from app.database.connect import get_connection
import sqlite3
from typing import TypedDict


class ActiveDose(TypedDict):
    medication: str
    dose_value: float
    start_date: str
    price: int
    id: int

def get_user_by_id(tg_id : int) -> dict | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()

    if user is None:
        return None

    return  dict(user)


def get_active_dose_by_user_id(tg_id: int) -> ActiveDose | None:

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

    if dose is None:
        return None
    return dict(dose)


def get_first_therapy_date(tg_id: int):
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
    return [dict(order) for order in orders]

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
    data = cursor.fetchall()
    if data is None:
        return None

    return [dict(item) for item in data]

def update_weight(tg_id: int, new_weight: float):
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


def add_order(tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status = "NEW"):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO orders (
                tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status))
    except sqlite3.Error as error:
        print(error)
        connection.close()
        return False

    connection.commit()
    connection.close()
    return True
