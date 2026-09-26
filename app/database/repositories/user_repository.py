import sqlite3
from app.database.connection import get_connection

# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration
class UserRepository:

    def create(self, *kwargs) -> bool:
        pass

    def get_by_tg_id(self, tg_id: int) -> dict | None:
        pass

    def get_by_full_name(self, full_name: str) -> dict | None:
        pass

    def get_by_phone(self, phone: str) -> dict | None:
        pass


    def create(self,
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
            user_id = cursor.lastrowid
            return user_id
        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()


    def get_by_tg_id(self, tg_id: int) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
            user = cursor.fetchone()
            connection.close()
            return dict(user) if user is not None else None

        finally:
            connection.close()

    def get_by_full_name(self, full_name: str) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE full_name = ?", (full_name,))
            user = cursor.fetchone()
            return dict(user) if user is not None else None

        finally:
            connection.close()

    def get_by_phone(self, phone_number: str) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE phone = ?", (phone_number,))
            user = cursor.fetchone()
            return dict(user) if user is not None else None

        finally:
            connection.close()

user_repository = UserRepository()