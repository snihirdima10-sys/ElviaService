from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_user_cart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Результати check-in", callback_data="checkins:page:0")],
            [InlineKeyboardButton(text="Змінити дозування", callback_data="change_dose")],
            [InlineKeyboardButton(text="Історія терапії", callback_data="therapy_history")],
            [InlineKeyboardButton(text="Головне меню", callback_data="admin_main_menu")],
        ]
    )


def build_patients_keyboard(patients: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for patient in patients:
        builder.add(InlineKeyboardButton(text=f"{patient["full_name"]} {patient["phone"]}", callback_data=f"patient:{patient["id"]}"))

    builder.adjust(1)
    return builder.as_markup()


def get_therapy_history_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Карта пацієнта", callback_data="show_card_of_patient")],
            [InlineKeyboardButton(text="Головне меню", callback_data="admin_main_menu")]
        ]
    )


def build_doses_keyboard(doses: list):
    builder = InlineKeyboardBuilder()

    for dose in doses:
            builder.add(InlineKeyboardButton(text=f"{dose["medication"]} - {dose["dose_value"]}",
                                             callback_data=f"dose_id:{dose["id"]}"))

    builder.adjust(1)
    return builder.as_markup()


def get_confirm_change_dose_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_dose")],
            [InlineKeyboardButton(text="⬅️ Обрати інше", callback_data="choose_another_dose")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_choose_dose")]
        ]
    )
