from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message,  ReplyKeyboardMarkup, KeyboardButton

from app.database.repositories.order_repository import order_repository
from app.utils.formatter import format_weeks


def get_my_orders_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True)

router = Router()

@router.message(StateFilter(None), F.text == "📦 МоЇ замовлення")
async def show_user_orders(message: Message):
    if message.from_user is None:
        return

    tg_id = message.from_user.id
    orders = order_repository.get_all_by_tg_id(tg_id)

    if orders is None:
        await message.answer("ТУТ ПУСТА")
        return


    orders_text = ""

    i = 1
    for order in orders:
        date = datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S").date()
        date = date.strftime("%Y.%m.%d")
        orders_text += (
            f"🪴<b>Замовлення №{order["id"]}</b>\n\n"
            f"{order["medication"]} - {order["dose_value"]} мг\n"
            f"Курс: {format_weeks(order["weeks_count"])}\n"
            f"Сума: {order["total_price"]} грн\n"
            f"Дата: {date}\n\n")

        if i < len(orders):
            i += 1
            orders_text += "────────────────────────\n\n"

    await message.answer("📦 <b>Історія замовлень</b>\n\n" + orders_text, reply_markup=get_my_orders_keyboard())