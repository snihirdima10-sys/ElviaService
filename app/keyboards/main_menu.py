from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🌿 Моя терапія"),
         ],
        [
            KeyboardButton(text="📊 Мій прогрес"),
            KeyboardButton(text="⚖️ Оновити вагу"),
        ],
        [
            KeyboardButton(text="📚 Корисна інформація"),
            KeyboardButton(text="🛒 Зробити замовлення")
        ],
        [KeyboardButton(text="👩‍⚕️ Зв’язатися з лікарем")]
    ],
    resize_keyboard=True
)