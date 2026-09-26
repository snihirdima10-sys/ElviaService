from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:

    main_menu_keyboard = ReplyKeyboardMarkup(
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
        ], resize_keyboard=True
    )
    return main_menu_keyboard
