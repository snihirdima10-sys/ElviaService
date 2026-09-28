from app.database.connection import  get_connection

# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration
class DoseRepository:
    def get_by_id(self, dose_id: int) -> dict:
        pass

    def get_all(self) -> list:
        pass

    def get_by_id(self, dose_id: int) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""SELECT * FROM doses WHERE id = ?""", (dose_id,))
            dose = cursor.fetchone()
            connection.close()
            return dict(dose) if dose is not None else None

        finally:
            connection.close()


    def get_all(self):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT * FROM doses""")

            doses = cursor.fetchall()
            return [dict(dose) for dose in doses] if doses else None

        finally:
            connection.close()

dose_repository = DoseRepository()


