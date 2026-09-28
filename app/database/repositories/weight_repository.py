import sqlite3

# noinspection PyRedeclaration
from app.database.connection import get_connection


# noinspection PyMethodMayBeStatic
class WeightRepository:
    def update_by_tg_id(self, tg_id: int, new_weight: float) -> int:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO weight_history (user_id, weight)
                SELECT users.id, ?
                FROM users
                WHERE users.tg_id = ?
                """, (new_weight, tg_id)
            )

            connection.commit()
            weight_id = cursor.lastrowid
            return weight_id

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()

weight_repository = WeightRepository()