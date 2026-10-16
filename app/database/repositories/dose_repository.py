import sqlite3

from app.database.connection import  get_connection
from app.models.dose import Dose
from app.services.order_catalog import MEDICATION


# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration
class DoseRepository:
    def get_or_create_catalog_dose(self, dose_value: float) -> Dose:
        connection = get_connection()
        try:
            with connection:
                connection.execute(
                    "INSERT INTO doses (medication, dose_value, price) VALUES (?, ?, ?) "
                    "ON CONFLICT(medication, dose_value) DO NOTHING",
                    (MEDICATION, dose_value, int(dose_value * 1000)),
                )
                row = connection.execute(
                    "SELECT * FROM doses WHERE medication = ? AND dose_value = ?",
                    (MEDICATION, dose_value),
                ).fetchone()
                return self._map_to_dose(row)
        finally:
            connection.close()

    def deactivate(self, dose_id: int) -> bool:
        connection = get_connection()
        try:
            with connection:
                return connection.execute(
                    "UPDATE doses SET is_active = 0 WHERE id = ? AND is_active = 1", (dose_id,)
                ).rowcount > 0
        finally:
            connection.close()

    def get_active_by_id(self, dose_id: int) -> Dose | None:
        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT * FROM doses WHERE id = ? AND is_active = 1", (dose_id,)
            ).fetchone()
            return self._map_to_dose(row) if row else None
        finally:
            connection.close()

    def create(self, medication: str, dose_value: float, price: int) -> int:
        connection = get_connection()
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO doses (medication, dose_value, price) VALUES (?, ?, ?)",
                    (medication, dose_value, price),
                )
                return cursor.lastrowid
        finally:
            connection.close()

    def get_by_id(self, dose_id: int) -> Dose | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
            SELECT 
                id,
                medication,
                dose_value,
                price
            FROM doses 
            WHERE id = ?""", (dose_id,))
            dose = cursor.fetchone()
            return self._map_to_dose(dose) if dose else None

        finally:
            connection.close()


    def get_all(self) -> list[Dose] | None:
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM doses WHERE is_active = 1 ORDER BY medication, dose_value, id")

            doses = cursor.fetchall()
            return [self._map_to_dose(dose) for dose in doses] if doses else None

        finally:
            connection.close()

    def _map_to_dose(self, row: sqlite3.Row) -> Dose:
        return Dose(
            id=row["id"],
            medication=row["medication"],
            dose_value=row["dose_value"],
            price=row["price"],
        )

dose_repository = DoseRepository()


