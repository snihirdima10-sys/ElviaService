from aiogram import F, Router
from aiogram.types import Message,  ReplyKeyboardMarkup, KeyboardButton

from app.database.service import get_user_orders


def format_weeks(weeks: int) -> str:
    if weeks % 10 == 1 and weeks % 100 != 11:
        word = "тиждень"
    elif weeks % 10 in [2, 3, 4] and weeks % 100 not in [12, 13, 14]:
        word = "тижні"
    else:
        word = "тижнів"

    return f"{weeks} {word}"

router = Router()


@router.message(F.text == "📦 МоЇ замовлення")
async def show_user_orders(message: Message):
    if message.from_user is None:
        return
    tg_id = message.from_user.id
    orders = get_user_orders(tg_id)

    if orders is None:
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True)

    orders_text = ""
    for order in orders:

        orders_text += (
            f"1. {order["medication"]} • {order["dose_value"]} мг • {order["total_price"]} грн\n"
            f"📅 {order["created_at"]}\n"
            f"Курс: {format_weeks(order["weeks_count"])}\n\n"
        )

    await message.answer("📦 Історія замовлень\n\n" + orders_text, reply_markup=keyboard)