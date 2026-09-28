from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram import Router
from config import CHANNEL_URL


def get_useful_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
        [KeyboardButton(text="🏠 Головне меню")]
        ],
        resize_keyboard=True,
    )

router = Router()


@router.message(StateFilter(None), F.text == "📚 Корисна інформація")
async def useful_info(message: Message):
    await message.answer(
        f'📚 <b>Корисна інформація</b>\n\n'
        "У нашому Telegram-каналі ми зібрали матеріали, які допоможуть вам краще розуміти терапію та почуватися впевненіше на кожному її етапі.\n\n"
        "Тут ви знайдете інформацію про <b>харчування, фізичну активність, можливі побічні реакції, рекомендації</b> та відповіді на поширені запитання 🗯️\n"
        f'👉 <a href="{CHANNEL_URL}">Перейти до каналу</a>',
        parse_mode="HTML",
        reply_markup=get_useful_keyboard()
    )