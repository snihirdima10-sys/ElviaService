
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