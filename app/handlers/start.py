from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🩺 Зв'язатися з лікарем")],
        [
            KeyboardButton(text="📝 Моя анкета"),
            KeyboardButton(text="💉 Зробити замовлення")
        ],
        [

            KeyboardButton(text="📊 Мій прогрес"),
            KeyboardButton(text="📚 Корисна інформація")
        ]
    ],
    resize_keyboard=True
)

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("""
        Вітаємо в Elvia 🤍
Ваш особистий простір для консультацій, контролю прогресу та медичного супроводу.  
Натисніть кнопку нижче, щоб продовжити.
    """, reply_markup=main_menu)