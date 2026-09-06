from aiogram import F
from aiogram.types import Message
from aiogram import Router
from config import CHANNEL_URL
from app.keyboards.back_menu import back_menu

router = Router()

@router.message(F.text == "📚 Корисна інформація")
async def useful_info(message: Message):
    await message.answer(
        f'📚 <b>Корисна інформація</b>\n\n'
        f'У нашому Telegram-каналі ви знайдете корисні матеріали про '
        f'<b>терапію, харчування, фізичну активність, можливі побічні реакції</b> '
        f'та відповіді на часті запитання.\n\n'
        f'👉 <a href="{CHANNEL_URL}">Перейти до каналу</a>',
        parse_mode="HTML",
        reply_markup=back_menu
    )