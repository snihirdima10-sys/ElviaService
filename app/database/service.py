from app.database.connect import get_connection
import sqlite3

def get_user_by_id(tg_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()

    if user is None:
        return None

    return  dict(user)

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



def get_user_dose_history(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM user_doses WHERE id = ?", (user_id,))
    return dict(cursor.fetchone())

def get_active_dose(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT doses.dose_value, doses.medication, doses.price
    FROM user_doses 
    JOIN doses ON doses.id = user_doses.dose_id
    WHERE user_id = ? AND status = 'active'""", (user_id,))
    return dict(cursor.fetchone())