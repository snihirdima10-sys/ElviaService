from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import URL_GOOGLE_FORM


def get_inline_link_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заповнити анкету", url=URL_GOOGLE_FORM)]
        ]
    )