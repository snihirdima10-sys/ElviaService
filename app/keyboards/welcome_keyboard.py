from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌿 Розпочати", callback_data="start_registration")],
            [InlineKeyboardButton(text="Політика конфіденційності", callback_data="privacy_policy")]
        ]
    )
