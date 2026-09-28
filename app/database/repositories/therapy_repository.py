
from app.database.connection import get_connection

# noinspection PyMethodMayBeStatic
# noinspection PyRedeclaration
class TherapyRepository:
    def get_active_by_tg_id(self, tg_id: int) -> dict | None:
        pass

    def get_first_by_tg_id(self, tg_id: int) -> dict | None:
        pass

    def get_history_by_tg_id(self, tg_id: int) -> list | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT 
                    user_doses.*,
                    doses.medication,
                    doses.dose_value
                    
                FROM user_doses
                
                JOIN doses
                    ON doses.id = user_doses.dose_id
                    
                JOIN users
                    ON users.id = user_doses.user_id
                
                WHERE users.tg_id = ?
                    AND user_doses.status = 'completed'
            """, (tg_id,)
            )

            therapies = cursor.fetchall()
            connection.close()
            return [dict(therapy) for therapy in therapies] if therapies else None

        finally:
            connection.close()

    def get_active_by_tg_id(self, tg_id: int) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                    SELECT
                        user_doses.*,
                        doses.*,
                        users.current_weight
                        
                    FROM user_doses
                    
                    JOIN users 
                        ON users.id = user_doses.user_id
                        
                    JOIN doses
                        ON doses.id = user_doses.dose_id
                        
                    WHERE users.tg_id = ?
                      AND user_doses.status = 'active'
                """, (tg_id,))

            therapy = cursor.fetchone()
            connection.close()
            return dict(therapy) if therapy else None

        finally:
            connection.close()

    def get_first_by_tg_id(self, tg_id: int) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                SELECT user_doses.*
                FROM user_doses
                JOIN users
                    ON users.id = user_doses.user_id
                WHERE users.tg_id = ?
                ORDER BY user_doses.start_date ASC
                LIMIT 1
                """,
                (tg_id,)
            )

            therapy = cursor.fetchone()
            connection.close()
            return dict(therapy) if therapy else None

        finally:
            connection.close()


therapy_repository = TherapyRepository()



