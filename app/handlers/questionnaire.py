from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from  aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.keyboards.main_menu import main_menu
from config import URL_GOOGLE_FORM

questionnaire_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

questionnaire_link_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Заповнити анкету",
                url=URL_GOOGLE_FORM
            )
        ]
    ]
)

router = Router()

@router.message(F.text == "📝 Моя анкета")
async def questionnaire_handler(message: Message):
    await message.answer(
        "📝 Моя анкета:",
        reply_markup=questionnaire_keyboard
    )

    await message.answer("""
    Щоб лікар міг попередньо оцінити ваш стан і підготуватися до консультації, будь ласка, заповніть анкету за посиланням нижче.  
Вказуйте лише актуальну інформацію про стан здоров’я, препарати та попередній досвід терапії.  
Не надсилайте медичні дані звичайним повідомленням у чаті — використовуйте форму за посиланням.
    """, reply_markup=questionnaire_link_keyboard)


@router.message(F.text == "⬅️ Назад")
async def back_to_menu(message: Message):
    await message.answer('Головне меню:', reply_markup=main_menu)