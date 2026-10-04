from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import CHECKIN_TEST_BUTTON_ENABLED

CHECKIN_TEST_MENU = "🧪 Check-in (тест)"

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:

    main_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            # *([[KeyboardButton(text=CHECKIN_TEST_MENU)]] if CHECKIN_TEST_BUTTON_ENABLED else []),
            [
                KeyboardButton(text="🌿 Моя терапія"),
            ],
            [
                KeyboardButton(text="📊 Мій прогрес"),
                KeyboardButton(text="👤 Профіль"),
            ],
            [
                KeyboardButton(text="📚 Корисна інформація"),
                KeyboardButton(text="🛒 Зробити замовлення")
            ],
            [
                KeyboardButton(text="📋 Історія терапії"),
                KeyboardButton(text="📦 Мої замовлення")
            ],
            [KeyboardButton(text="👩‍⚕️ Зв’язатися з лікарем")],
                    ], resize_keyboard=True
        , one_time_keyboard=False, is_persistent=True
    )
    return main_menu_keyboard
