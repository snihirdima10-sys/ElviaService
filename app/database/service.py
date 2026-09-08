from app.database.connect import get_connection


def get_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return  dict(cursor.fetchone())

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