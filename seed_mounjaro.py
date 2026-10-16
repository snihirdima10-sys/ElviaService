"""Delete all old doses and create 19 new Mounjaro doses.

Usage: python seed_mounjaro.py
Existing orders and therapies are reassigned by matching dose_value.
If a referenced dose is outside the new list, the transaction is aborted.
"""
import sqlite3
from datetime import datetime
from uuid import uuid4

from config import DB_PATH
from app.database.connection import get_connection
from app.database.init_db import init_db

MEDICATION = "Мунджаро"
DOSES = [(MEDICATION, half_mg / 2, half_mg * 500) for half_mg in range(2, 21)]


def seed_mounjaro() -> None:
    connection = get_connection()
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            old_doses = connection.execute("SELECT id, dose_value FROM doses").fetchall()
            referenced = {row[0] for row in connection.execute(
                "SELECT dose_id FROM orders UNION SELECT dose_id FROM therapies"
            )}
            supported_values = {value for _, value, _ in DOSES}
            unmatched = [row["dose_value"] for row in old_doses
                         if row["id"] in referenced and row["dose_value"] not in supported_values]
            if unmatched:
                values = ", ".join(f"{value:g}" for value in sorted(set(unmatched)))
                raise ValueError(
                    f"Неможливо замінити пов’язані дозування: {values} мг. "
                    "Їх немає в новому списку. Базу не змінено."
                )

            # Temporary medication name avoids unique conflicts with old Mounjaro rows.
            temporary_name = "mounjaro-seed-" + uuid4().hex
            new_ids = {}
            for _, value, price in DOSES:
                cursor = connection.execute(
                    "INSERT INTO doses (medication, dose_value, price, is_active) VALUES (?, ?, ?, 1)",
                    (temporary_name, value, price),
                )
                new_ids[value] = cursor.lastrowid
            for old in old_doses:
                if old["id"] in referenced:
                    new_id = new_ids[old["dose_value"]]
                    connection.execute("UPDATE orders SET dose_id = ? WHERE dose_id = ?", (new_id, old["id"]))
                    connection.execute("UPDATE therapies SET dose_id = ? WHERE dose_id = ?", (new_id, old["id"]))
            connection.executemany("DELETE FROM doses WHERE id = ?", [(row["id"],) for row in old_doses])
            connection.execute("UPDATE doses SET medication = ? WHERE medication = ?", (MEDICATION, temporary_name))
    finally:
        connection.close()


def main() -> None:
    if DB_PATH.exists():
        backup_path = DB_PATH.with_name(
            f"db-before-mounjaro-{datetime.now():%Y%m%d-%H%M%S-%f}.db"
        )
        source = get_connection()
        try:
            destination = sqlite3.connect(backup_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()
        print(f"Резервна копія: {backup_path}")
    init_db()
    seed_mounjaro()
    print("Старі дозування видалено. Створено 19 нових дозувань Мунджаро, від 1 до 10 мг.")
    print("Ціна: 1 мг = 1 000 грн. Замовлення та призначення переприв’язано за кількістю мг.")


if __name__ == "__main__":
    main()
