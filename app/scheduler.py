from datetime import date, timedelta
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.database.connect import get_connection


keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")],
])

async def request_weight(bot: Bot):
    connection = get_connection()
    cursor = connection.cursor()

    today = date.today().isoformat()

    cursor.execute("""
        SELECT tg_id
        FROM users
        WHERE next_weight_request_at <= ?
    """, (today,))

    users = cursor.fetchall()

    for user in users:
        tg_id = user["tg_id"]

        try:
            await bot.send_message(
                tg_id,
                "⏰ Час оновити вагу\n\n"
                "Зважтеся вранці натщесерце та внесіть актуальний показник у бот.",
                reply_markup=keyboard
            )

            next_date = date.today() + timedelta(days=7)

            cursor.execute("""
                UPDATE users
                SET next_weight_request_at = ?
                WHERE tg_id = ?
            """, (next_date.isoformat(), tg_id))

        except Exception as error:
            print(f"Помилка надсилання {tg_id}: {error}")

    connection.commit()
    connection.close()