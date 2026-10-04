from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.container import Services
from app.keyboards.user import get_therapy_history_keyboard
from app.texts.user import format_therapy_history

router = Router()


@router.message(StateFilter(None), F.text == "📋 Історія терапії")
async def therapy_history(message: Message, services: Services):
    if message.from_user is None:
        return
    tg_id = message.from_user.id

    user = services.user.get_user_by_tg_id(tg_id)
    if user is None:
        return

    active_therapy = services.therapy.get_active_therapy_by_user_id(user.id)
    therapies_history = services.therapy.get_history_therapy_by_user_id(user.id)


    await message.answer(
        format_therapy_history(
            user=user,
            active_therapy=active_therapy,
            therapies_history=therapies_history,
        ), reply_markup=get_therapy_history_keyboard(), parse_mode="HTML"
    )
