import sqlite3
from datetime import date

from app.database.connection import get_connection
from models.dose import Dose
from models.therapy import Therapy, TherapyStatus


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
        pass

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
    ) -> None:
        """Створює терапію."""
        pass

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



