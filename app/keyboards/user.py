from app.utils.formatter import format_money
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton


def get_therapy_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Історія терапії")],
            [KeyboardButton(text="🏠 Головне меню")],
        ], resize_keyboard=True
    )

def get_therapy_history_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True)


def get_show_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:update_weight")]
        ]
    )


def get_confirm_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_weight")],
        [InlineKeyboardButton(text="🔄 Змінити вагу", callback_data="repeat_weight")],
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:update_weight")]
        ]
    )


def get_cancel_update_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:update_weight")]
    ])

def build_select_period_keyboard(dose_price):
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"1 тиждень — {format_money(dose_price)} грн",
                    callback_data="period:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"2 тиждень — {format_money(2 * dose_price * 0.9)} грн",
                    callback_data="period:2"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"4 тиждень — {format_money(4 * dose_price * 0.8)} грн",
                    callback_data="period:4"
                )
            ],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
        ])
    return inline_keyboard

def get_order_terms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Продовжити", callback_data="accept_order_terms")],
        [InlineKeyboardButton(text="🔄 Змінити період", callback_data="change_period")],
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")],
    ])

def get_cancel_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
        ]
    )

def get_show_order_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити замовлення",
                    callback_data="confirm_order")
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Змінити дані",
                    callback_data="edit_delivery_data")
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Скасувати",
                    callback_data="cancel:order")
            ]
    ])

def get_payment_details_keyboard(iban: str = '', recipient: str = '', purpose: str = '') -> InlineKeyboardMarkup:
    rows = []
    for label, value in [('📋 Копіювати IBAN', iban), ('📋 Копіювати отримувача', recipient),
                         ('📋 Копіювати призначення', purpose)]:
        # Telegram copy buttons accept 1–256 characters. Never truncate banking details.
        if value and len(value) <= 256:
            rows.append([InlineKeyboardButton(text=label, copy_text=CopyTextButton(text=value))])
    rows.extend([
            [InlineKeyboardButton(text="✅ Оплачено", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_success_create_order() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Мої замовлення")],
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True
    )

def get_delivery_methods_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Відділення", callback_data="method:branch")],
            [InlineKeyboardButton(text="Поштомат", callback_data="method:parcel_locker")],
            [InlineKeyboardButton(text="Адресна доставка", callback_data="method:courier_delivery")],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")],
        ]
    )
