from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from app.container import Services
from app.keyboards.user import get_therapy_keyboard
from app.texts.user import format_therapy


router = Router()


@router.message(StateFilter(None), F.text == "🌿 Моя терапія")
async def show_therapy(message: Message, services :Services):
    if message.from_user is None:
        return
    tg_id = message.from_user.id

    user_id = services.user.get_user_id_by_tg_id(tg_id)
    if user_id is None:
        return

    active_therapy = services.therapy.get_active_therapy_by_user_id(user_id)
    planned_therapy = services.therapy.get_planned_therapy_by_user_id(user_id)

    text = format_therapy(
        active_therapy = active_therapy,
        planned_therapy = planned_therapy
    )

    await message.answer(text, reply_markup=get_therapy_keyboard())