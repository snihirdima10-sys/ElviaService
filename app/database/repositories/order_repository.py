import sqlite3
from datetime import datetime

from app.database.connection import get_connection
from app.models.dose import Dose
from app.models.order import Order, OrderStatus


# noinspection PyRedeclaration
# noinspection PyMethodMayBeStatic
class OrderRepository:
    def get_all_by_user_id(self, user_id: int) -> list[Order]:
        """Повертраэ список замовлень користувача"""

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT 
                    orders.id,
                    orders.user_id,
                    orders.dose_id,
                    orders.weeks_count,
                    orders.discount,
                    orders.total_price,
                    orders.delivery_data,
                    orders.status,
                    orders.created_at,
                    
                    doses.id AS dose_id,
                    doses.medication,
                    doses.dose_value,
                    doses.price
                FROM orders
                JOIN doses
                    ON doses.id = orders.dose_id
                WHERE user_id = ?        
            """, (user_id,))

            rows = cursor.fetchall()
            if rows is None:
                return []
            return [self._map_to_order(row) for row in rows]

        finally:
            connection.close()


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
                    users.full_name,
                    users.phone AS user_phone
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
                
                JOIN users
                    ON orders.user_id = users.id
                    
                JOIN doses
                    ON doses.id = orders.dose_id
                    
                WHERE tg_id = ?
                """, (tg_id,)
            )

            orders = cursor.fetchall()
            connection.close()
            return [dict(order) for order in orders] if orders else None

        finally:
            connection.close()

    def get_all_by_status(self, status: str | None = None) -> list[dict]:
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
                WHERE (? IS NULL OR orders.status = ?)
                ORDER BY orders.created_at DESC, orders.id DESC""",
                (status, status)
            )

            orders = cursor.fetchall()
            connection.close()
            return [dict(order) for order in orders]

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
               user_id: int,
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
                    user_id,
                    dose_id,
                    weeks_count,
                    discount,
                    total_price,
                    delivery_data,
                    status
                )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                dose_id,
                weeks_count,
                discount,
                total_price,
                delivery_data,
                status,

            ))

            order_id = cursor.lastrowid
            connection.commit()

            return order_id

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()

    def _map_to_order(self, row: sqlite3.Row) -> Order:
        return Order(
            id=row['id'],
            user_id=row['user_id'],
            dose=Dose(
                id=row['dose_id'],
                medication=row['medication'],
                dose_value=row['dose_value'],
                price=row['price']
            ),
            weeks_count=row['weeks_count'],
            discount=row['discount'],
            total_price=row['total_price'],
            delivery_data=row['delivery_data'],
            status=OrderStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']).date(),
        )


order_repository = OrderRepository()


