from aiogram import Router
from aiogram import F
from aiogram.types  import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.keyboards.back_menu import back_menu
from config import DOCTOR_URL

router = Router()


@router.message(F.text == "🩺 Зв'язатися з лікарем")
async def contact_doctor(message: Message):
    await message.answer(
        f'🩺 <b>Зв’язатися з лікарем</b>\n\n'
        f'Якщо у вас є запитання щодо <b>самопочуття, терапії або рекомендацій</b>, '
        f'ви можете написати лікарю напряму.\n\n'
        f'👉 <a href="{DOCTOR_URL}">Профіль лікаря</a>',
        parse_mode="HTML", reply_markup=back_menu
    )