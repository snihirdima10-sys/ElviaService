import sqlite3
from datetime import datetime, timedelta, date
from app.database.connection import get_connection
from models.user import User


# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration



class UserRepository:

    def get_by_id(self, user_id: int) -> User | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
            SELECT 
                id,
                tg_id,
                full_name,
                phone,
                height,
                start_weight,
                current_weight,
                target_weight,
                next_weight_request_at,
                created_at
            FROM users
            WHERE id = ?
            """, (user_id,))

            row = cursor.fetchone()
            return self._map_to_user(row) if row else None

        finally:
            connection.close()

    def get_user_id_by_tg_id(self, tg_id: int) -> int | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
            SELECT *
            FROM users 
            WHERE tg_id = ?
            """, (tg_id,))

            row = cursor.fetchone()
            return row["id"] if row else None

        finally:
            connection.close()

    def _map_to_user(self, row: sqlite3.Row) -> User | None:
        return User(
            id=row['id'],
            tg_id=row['tg_id'],
            full_name=row['full_name'],
            phone=row['phone'],
            height=row['height'],
            start_weight=row['start_weight'],
            current_weight=row['current_weight'],
            target_weight=row['target_weight'],
            next_weight_request_at=row['next_weight_request_at'],
            created_at=datetime.fromisoformat(row['created_at']).date()
        )

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

    def update_current_weight_by_user_id(self, user_id: int, new_weight: float, next_weight_request_at: str) -> int | None:
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
            UPDATE users
            SET current_weight = ?,
                next_weight_request_at = ?
            WHERE id = ?
            """, (new_weight, next_weight_request_at, user_id))

            connection.commit()
            row = cursor.rowcount
            return row

        except sqlite3.Error:
            connection.rollback()

        finally:
            connection.close()


    def search_by_name_or_phone(self, query: str) -> list[dict]:
        connection = get_connection()
        cursor = connection.cursor()

        query = query.strip()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE full_name LIKE ?
               OR phone LIKE ?
            ORDER BY full_name
            LIMIT 10
        """, (
            f"%{query}%",
            f"%{query}%"
        ))

        patients = cursor.fetchall()
        connection.close()

        return [dict(patient) for patient in patients]


user_repository = UserRepository()