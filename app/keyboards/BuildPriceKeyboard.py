from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.order_catalog import OFFERS, dose_label
from app.utils.formatter import format_money


class OrderMenuCallback(CallbackData, prefix="order_menu"):
    action: str
    value: str = ""


def button(text: str, action: str, value: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text, callback_data=OrderMenuCallback(action=action, value=value).pack())


def navigation(back: str = "menu") -> list[list[InlineKeyboardButton]]:
    return [[button("← Назад", back)],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="user_main_menu")]]


def build_order_menu(has_therapy: bool) -> InlineKeyboardMarkup:
    rows = [[button("🎁 Акційні пропозиції", "offers")]]
    if has_therapy:
        rows.append([button("📋 Обрати поточне призначення", "current")])
    rows.append([button("💉 Обрати дозування", "doses")])
    rows.append([InlineKeyboardButton(text="🏠 Головне меню", callback_data="user_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_price_keyboard() -> InlineKeyboardMarkup:
    buttons = [button(f"{dose_label(n / 2)} мг", "dose", str(n)) for n in range(2, 21)]
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=rows + navigation())


def build_offers_keyboard(first_available: bool = True) -> InlineKeyboardMarkup:
    rows = [[button(f"{offer.title} — {format_money(offer.price)} грн", "offer", code)]
            for code, offer in OFFERS.items() if code != "first" or first_available]
    return InlineKeyboardMarkup(inline_keyboard=rows + navigation())


def build_selection_keyboard(kind: str, value: str) -> InlineKeyboardMarkup:
    # Offer details intentionally contain exactly two buttons.
    rows = [[button("🛒 Оформити замовлення", "checkout_" + kind, value)],
            [button("← Назад", "offers" if kind == "offer" else "doses" if kind == "dose" else "menu")]]
    if kind != "offer":
        rows.append([InlineKeyboardButton(text="🏠 Головне меню", callback_data="user_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
