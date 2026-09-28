from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_privacy_policy_keyboard() -> InlineKeyboardMarkup:
    return  InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_welcome_message")],
        ]
    )