from aiogram import Router
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types  import Message, KeyboardButton, ReplyKeyboardMarkup
from config import DOCTOR_URL

router = Router()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Головне меню")]
    ],
    resize_keyboard=True
)

@router.message(StateFilter(None), F.text == "👩‍⚕️ Зв’язатися з лікарем")
async def contact_doctor(message: Message):
    await message.answer(
        f'👩‍⚕️ <b>Зв’язатися з лікарем</b>\n\n'
       "Якщо у вас виникли запитання щодо терапії, самопочуття або рекомендацій, ви можете звернутися безпосередньо до лікаря.\n\n"
        "<i>Не соромтеся ставити запитання — важливо, щоб на кожному етапі терапії ви почувалися впевнено та мали необхідну підтримку</i> 🤍\n"
        f'👉 <a href="{DOCTOR_URL}">Профіль лікаря</a>',
        parse_mode="HTML", reply_markup=keyboard
    )