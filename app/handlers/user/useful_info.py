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
        f'У нашому Telegram-каналі ви знайдете корисні матеріали про '
        f'<b>терапію, харчування, фізичну активність, можливі побічні реакції</b> '
        f'та відповіді на часті запитання.\n\n'
        f'👉 <a href="{CHANNEL_URL}">Перейти до каналу</a>',
        parse_mode="HTML",
        reply_markup=get_useful_keyboard()
    )