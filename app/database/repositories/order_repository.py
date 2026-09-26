import sqlite3

from app.database.connection import get_connection


# noinspection PyRedeclaration
# noinspection PyMethodMayBeStatic
class OrderRepository:
    def get_by_id(self, order_id: int) -> dict | None:
        pass

    def get_all_by_tg_id(self, tg_id: int) -> list| None:
        pass

    def get_all_by_status(self, status: str) -> list| None:
        pass

    def update_status(self, order_id: int, status: str) -> bool:
        pass

    def create(self,
               tg_id: int,
               user_phone: str,
               dose_id: int,
               weeks_count: int,
               discount: int,
               total_price: float,
               delivery_data: str,
               status: str
    ) -> bool:
        pass

    def get_by_id(self, order_id: int) -> dict | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    orders.*,
                    doses.medication,
                    doses.dose_value,
                    users.full_name
                FROM orders
                JOIN doses
                    ON orders.dose_id = doses.id
                JOIN users
                    ON orders.user_id = users.id
                WHERE orders.id = ?
                """,
                (order_id,)
            )
            order = cursor.fetchone()
            connection.close()
            return dict(order) if order is not None else None

        finally:
            connection.close()

    def get_all_by_tg_id(self, tg_id: int) -> list| None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    orders.*,
                    doses.medication,
                    doses.dose_value
                FROM orders
                JOIN doses ON doses.id = orders.dose_id
                WHERE tg_id = ?
                """, (tg_id,)
            )

            orders = cursor.fetchall()
            connection.close()
            return [dict(order) for order in orders] if orders else None

        finally:
            connection.close()

    def get_all_by_status(self, status: str) -> list | None:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT 
                    orders.*,
                    users.full_name 
                FROM orders
                JOIN users 
                    ON users.id = orders.user_id 
                WHERE status = ?""",
                (status,)
            )

            orders = cursor.fetchall()
            connection.close()
            return [dict(order) for order in orders] if orders else None

        finally:
            connection.close()

    def update_status(self, order_id: int, status: str) -> bool:
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )

            connection.commit()

            return cursor.rowcount > 0

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()


    def create(self,
               tg_id: int,
               user_phone: str,
               dose_id: int,
               weeks_count: int,
               discount: int,
               total_price: float,
               delivery_data: str,
               status: str
    ) -> int:
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                       INSERT INTO orders (
                           tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   """, (tg_id, user_phone, dose_id, weeks_count, discount, total_price, delivery_data, status))

            order_id = cursor.lastrowid
            connection.commit()

            return order_id

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()





