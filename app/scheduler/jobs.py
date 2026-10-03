import logging
from contextlib import closing
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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


async def request_weight(bot: Bot, today: date | None = None) -> int:
    """Advance each reminder date only after successful delivery."""
    today = today or local_today()
    with closing(get_connection()) as connection:
        users = connection.execute(
            """SELECT id, tg_id FROM users
               WHERE date(COALESCE(next_weight_request_at,
                   datetime(created_at, '+7 days'))) <= date(?)""",
            (today.isoformat(),),
        ).fetchall()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")
    ]])
    sent = 0
    for user in users:
        try:
            await bot.send_message(
                user["tg_id"],
                "⏰ Час оновити вагу\n\n"
                "Зважтеся вранці натщесерце та внесіть актуальний показник у бот.",
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception("Failed to send weight reminder to user %s", user["id"])
            continue
        next_date = (today + timedelta(days=7)).isoformat()
        with closing(get_connection()) as connection, connection:
            connection.execute(
                """UPDATE users SET next_weight_request_at = ?
                   WHERE id = ? AND (next_weight_request_at IS NULL
                       OR date(next_weight_request_at) < date(?))""",
                (next_date, user["id"], next_date),
            )
        sent += 1
    return sent
