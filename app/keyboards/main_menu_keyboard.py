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
            [
                KeyboardButton(text="📋 Історія терапії"),
                KeyboardButton(text="📦 Мої замовлення")
            ],
            [KeyboardButton(text="👩‍⚕️ Зв’язатися з лікарем")]
        ], resize_keyboard=True
        , one_time_keyboard=True
    )
    return main_menu_keyboard
