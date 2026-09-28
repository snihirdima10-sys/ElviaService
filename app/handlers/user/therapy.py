from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date
from app.database.repositories.therapy_repository import therapy_repository
from app.utils.formatter import format_weeks


router = Router()


def get_therapy_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Історія терапії")],
            [KeyboardButton(text="🏠 Головне меню")],
        ], resize_keyboard=True
    )


@router.message(StateFilter(None), F.text == "🌿 Моя терапія")
async def therapy(message: Message):
    if message.from_user is None:
        return
    tg_id = message.from_user.id
    active_therapy = therapy_repository.get_active_by_tg_id(tg_id)

    if active_therapy is None:
        await message.answer(
            "🌿 <b>Ваша терапія</b>\n\n"
            "Наразі активну терапію не призначено.\n"
            "Щоб розпочати терапію або отримати нове призначення, "
            "зверніться до лікаря.\n\n"
            "⚠Не починайте прийом препаратів і не змінюйте дозування самостійно."
        )
        return

    medication = active_therapy["medication"]
    dose_value = active_therapy["dose_value"]
    start_date = datetime.strptime(active_therapy["start_date"], "%Y-%m-%d").date()
    weeks = (date.today() - start_date).days // 7

    text = (
        f"🌿 <b>Ваша терапія</b>\n\n"
        f"<b>Препарат:</b> {medication}\n"
        f"<b>Актуальне дозування:</b> {dose_value}\n"
        f"<b>Початок терапії:</b> {start_date}\n"
        f"<b>Тривалість:</b> {format_weeks(weeks)}\n\n"
        f"⚠️ Будь-які зміни погоджуйте з лікарем"
    )

    await message.answer(text, reply_markup=get_therapy_keyboard())