from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.keyboards.main_menu import main_menu

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("""
        Вітаємо в Elvia 🤍
Ваш особистий простір для консультацій, контролю прогресу та медичного супроводу.  
Натисніть кнопку нижче, щоб продовжити.
    """, reply_markup=main_menu)