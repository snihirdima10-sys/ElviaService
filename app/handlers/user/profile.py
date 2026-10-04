from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.container import Services
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard

router = Router()


@router.message(F.text == "👤 Профіль")
async def show_profile(message: Message, state: FSMContext, services: Services):
    if message.from_user is None:
        return
    user = services.user.get_user_by_tg_id(message.from_user.id)
    if user is None:
        await message.answer("Щоб переглянути профіль, зареєструйтеся через /start.")
        return
    await state.clear()
    height = f"{user.height:g}".replace('.', ',')
    weight = f"{user.current_weight:.1f}".replace('.', ',')
    await message.answer(
        "👤 <b>Ваш профіль</b>\n\n"
        f"ID: <b>{user.tg_id}</b>\n"
        f"ПІБ: <b>{escape(user.full_name)}</b>\n"
        f"Номер телефону: <b>{escape(user.phone)}</b>\n\n"
        f"Зріст: <b>{height} см</b>\n"
        f"Поточна вага: <b>{weight} кг</b>",
        parse_mode="HTML", reply_markup=get_main_menu_keyboard(),
    )
