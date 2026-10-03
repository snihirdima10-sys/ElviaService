from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


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
            [InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")]
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
                    text=f"1 тиждень — {dose_price:.2f} грн",
                    callback_data="period:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"2 тиждень — {2 * dose_price * 0.9} грн",
                    callback_data="period:2"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"4 тиждень — {4 * dose_price * 0.8} грн",
                    callback_data="period:4"
                )
            ]
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

def get_payment_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оплачено", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
    ])

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
        ]
    )