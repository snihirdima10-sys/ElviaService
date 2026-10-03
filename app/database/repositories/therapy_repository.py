import sqlite3
from datetime import date

from app.database.connection import get_connection
from app.models.dose import Dose
from app.models.therapy import Therapy, TherapyStatus


# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration
class TherapyRepository:
    def get_active_by_user_id(self, user_id: int) -> Therapy | None:
        """Повертає активну терапію користувача"""

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    therapies.id,
                    therapies.user_id,
                    therapies.start_date,
                    therapies.end_date,
                    therapies.start_weight,
                    therapies.end_weight,
                    therapies.status,
                    
                    doses.id AS dose_id,
                    doses.medication,
                    doses.dose_value,   
                    doses.price
                    
                FROM therapies
                JOIN doses ON therapies.dose_id = doses.id
                
                WHERE therapies.user_id = ?
                    AND therapies.status = 'active'
            """,(user_id,))

            row = cursor.fetchone()
            if row is None:
                return None

            return self._map_to_therapy(row)
        finally:
            connection.close()

    def get_planned_by_user_id(self, user_id: int) -> Therapy | None:
        """Повертаэ заплановану терапіє користувача"""

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
            SELECT 
            therapies.id,
            therapies.user_id,
            therapies.start_date,
            therapies.end_date,
            therapies.start_weight,
            therapies.end_weight,
            therapies.status,
            
            doses.id AS dose_id,
            doses.medication,
            doses.dose_value,   
            doses.price
            
            FROM therapies
            
            JOIN doses 
                ON therapies.dose_id = doses.id
            
            WHERE therapies.user_id = ?
                AND therapies.status = 'planned'
            
            """, (user_id,))

            row = cursor.fetchone()

            if row is None:
                return None
            return self._map_to_therapy(row)

        finally:
            connection.close()

    def get_first_by_user_id(self, user_id: int) -> Therapy | None:
        """Повертає першу терапію користувача"""
        pass

    def get_history_by_user_id(self, user_id: int) -> list[Therapy] | None:
        """Повертає список завершених терапій"""
        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT therapies.*, doses.id AS dose_id,
                       doses.medication, doses.dose_value, doses.price
                FROM therapies JOIN doses ON doses.id = therapies.dose_id
                WHERE therapies.user_id = ? AND therapies.status = 'completed'
                ORDER BY therapies.start_date, therapies.id
            """, (user_id,)).fetchall()
            return [self._map_to_therapy(row) for row in rows]
        finally:
            connection.close()

    def complete_therapy(self, therapy_id: int, end_weight: float) -> None:
        """Позначає терапію завершеною, встановлює end_weight та end_date"""
        pass

    def activate_therapy(self, therapy_id: int) -> None:
        """Активує терапію."""
        pass

    def create_therapy(
            self,
            user_id: int,
            dose_id: int,
            start_date: str,
            start_weight: float,
            status: str,
    ) -> int:
        """Створює терапію."""
        connection = get_connection()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE therapies SET status = 'cancelled' WHERE user_id = ? AND status = 'planned'",
                    (user_id,),
                )
                if status == "active":
                    connection.execute(
                        """UPDATE therapies SET status = 'completed', end_date = ?, end_weight = ?
                           WHERE user_id = ? AND status = 'active'""",
                        (start_date, start_weight, user_id),
                    )
                cursor = connection.execute(
                    """INSERT INTO therapies (user_id, dose_id, start_date, start_weight, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, dose_id, start_date, start_weight, status),
                )
                return cursor.lastrowid
        finally:
            connection.close()

    def _map_to_therapy(self, row: sqlite3.Row) -> Therapy:
        return Therapy(
            id = row['id'],
            user_id=row['user_id'],
            dose = Dose(
                id = row['dose_id'],
                medication = row['medication'],
                dose_value = row['dose_value'],
                price = row['price'],
            ),
            start_date = date.fromisoformat(row["start_date"]),
            end_date = (date.fromisoformat(row["end_date"])
                        if row["end_date"]
                        else None
            ),
            start_weight = row['start_weight'],
            end_weight = row['end_weight'],
            status = TherapyStatus(row['status'])
        )


therapy_repository = TherapyRepository()



