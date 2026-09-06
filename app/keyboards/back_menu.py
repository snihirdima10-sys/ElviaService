from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

back_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)