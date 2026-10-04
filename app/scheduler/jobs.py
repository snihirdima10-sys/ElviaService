import logging
from contextlib import closing
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot

from app.database.connection import get_connection

logger = logging.getLogger(__name__)
TIMEZONE = ZoneInfo("Europe/Kyiv")


def local_today() -> date:
    return datetime.now(TIMEZONE).date()


async def activate_due_therapies(today: date | None = None) -> int:
    """Activate due stages atomically, including stages missed during downtime.

    The latest known weight is used; historical measurements are not inferred.
    """
    today = today or local_today()
    with closing(get_connection()) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        planned = connection.execute(
            """SELECT t.id, t.user_id, t.start_date, u.current_weight
               FROM therapies t JOIN users u ON u.id = t.user_id
               WHERE t.status = 'planned' AND date(t.start_date) <= date(?)
               ORDER BY t.start_date, t.id""",
            (today.isoformat(),),
        ).fetchall()
        for therapy in planned:
            connection.execute(
                """UPDATE therapies
                   SET status = 'completed', end_date = ?, end_weight = ?
                   WHERE user_id = ? AND status = 'active'""",
                (therapy["start_date"], therapy["current_weight"], therapy["user_id"]),
            )
            connection.execute(
                """UPDATE therapies SET status = 'active', start_weight = ?,
                   end_date = NULL, end_weight = NULL
                   WHERE id = ? AND status = 'planned'""",
                (therapy["current_weight"], therapy["id"]),
            )
    return len(planned)


async def request_checkins(bot: Bot, today: date | None = None) -> int:
    """Send due invitations daily until completion; only successful sends count."""
    from app.services.checkin_service import CheckinService
    from app.handlers.user.checkin import INTRO, intro_keyboard

    today = today or local_today()
    service = CheckinService(get_connection)
    with closing(get_connection()) as connection:
        users = connection.execute(
            """SELECT u.id, u.tg_id FROM users u
               LEFT JOIN weekly_checkins c ON c.user_id=u.id AND c.status='draft'
               WHERE (c.id IS NOT NULL OR date(COALESCE(u.next_checkin_at,
                   datetime(u.created_at, '+7 days'))) <= date(?))
               AND (c.last_reminded_on IS NULL OR date(c.last_reminded_on) < date(?))""",
            (today.isoformat(), today.isoformat()),
        ).fetchall()
    sent = 0
    for user in users:
        draft = service.begin(user['id'], today, from_reminder=True)
        if draft is None:
            continue
        try:
            await bot.send_message(user['tg_id'], INTRO, reply_markup=intro_keyboard())
        except Exception:
            logger.exception('Failed to send check-in reminder to user %s', user['id'])
            continue
        with closing(get_connection()) as connection, connection:
            connection.execute(
                "UPDATE weekly_checkins SET last_reminded_on=? WHERE id=? AND status='draft'",
                (today.isoformat(), draft['id']),
            )
        sent += 1
    return sent
