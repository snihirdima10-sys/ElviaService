

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message,  ReplyKeyboardMarkup, KeyboardButton

from app.container import Services
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.texts.user import format_orders_text


def get_my_orders_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True)

router = Router()

@router.message(StateFilter(None), F.text == "📦 Мої замовлення")
async def show_user_orders(message: Message, services: Services):
    if message.from_user is None:
        return
    tg_id = message.from_user.id
    user_id = services.user.get_user_id_by_tg_id(tg_id)
    if user_id is None:
        return

    orders = services.order.get_all_orders_by_user_id(user_id)

    if not orders:
        await message.answer(
            "📦 Замовлень поки немає\n\n"
            "У вас ще немає оформлених замовлень.\n\n"
            "Коли ви зробите перше замовлення, інформація про нього з’явиться в цьому розділі 🤍"
        , reply_markup=get_main_menu_keyboard()
        )
        return
    await message.answer(format_orders_text(orders=orders), reply_markup=get_my_orders_keyboard())