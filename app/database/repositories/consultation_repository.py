from contextlib import closing

from app.database.connection import get_connection


def get_or_create_request(user_id: int) -> dict:
    with closing(get_connection()) as connection, connection:
        connection.execute(
            "INSERT OR IGNORE INTO consultation_requests(user_id) VALUES (?)", (user_id,))
        return dict(connection.execute(
            "SELECT * FROM consultation_requests WHERE user_id = ? AND status IN ('payment', 'pending')",
            (user_id,),
        ).fetchone())


def get_request(request_id: int) -> dict | None:
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT c.*, u.tg_id FROM consultation_requests c JOIN users u ON u.id = c.user_id WHERE c.id = ?",
            (request_id,),
        ).fetchone()
        return dict(row) if row else None


def change_status(request_id: int, old_status: str, new_status: str) -> bool:
    with closing(get_connection()) as connection, connection:
        return connection.execute(
            "UPDATE consultation_requests SET status = ? WHERE id = ? AND status = ?",
            (new_status, request_id, old_status),
        ).rowcount == 1
