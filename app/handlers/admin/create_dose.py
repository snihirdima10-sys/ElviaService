import sqlite3
from html import escape
from math import isfinite

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.container import Services
from app.handlers.admin.delete_dose import show_doses
from app.utils.formatter import format_money

router = Router()


class CreateDoseState(StatesGroup):
    medication = State()
    value = State()
    price = State()
    confirm = State()


def keyboard(confirm=False):
    rows = []
    if confirm:
        rows.append([InlineKeyboardButton(text="✅ Створити", callback_data="create_dose:confirm")])
    rows.append([InlineKeyboardButton(text="↩️ До дозувань", callback_data="delete_dose:page:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "create_dose:start")
async def start_create_dose(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await state.clear()
    await state.set_state(CreateDoseState.medication)
    await query.message.edit_text("💉 <b>Нове дозування</b>\n\nВведіть назву препарату, наприклад: Mounjaro.",
                         parse_mode="HTML", reply_markup=keyboard())


@router.message(CreateDoseState.medication)
async def medication_input(message: Message, state: FSMContext):
    medication = (message.text or "").strip()
    if not 1 <= len(medication) <= 100:
        await message.answer("Введіть назву препарату від 1 до 100 символів.", reply_markup=keyboard())
        return
    await state.update_data(medication=medication)
    await state.set_state(CreateDoseState.value)
    await message.answer("Введіть дозування в мг, наприклад: 5 або 2,5.", reply_markup=keyboard())


@router.message(CreateDoseState.value)
async def value_input(message: Message, state: FSMContext):
    try:
        value = float((message.text or "").strip().replace(',', '.'))
    except ValueError:
        value = float('nan')
    if not isfinite(value) or value <= 0:
        await message.answer("Введіть додатне число в мг, наприклад: 2,5.", reply_markup=keyboard())
        return
    await state.update_data(dose_value=value)
    await state.set_state(CreateDoseState.price)
    await message.answer("Введіть ціну за 1 тиждень у цілих гривнях, без знижки, наприклад: 4000.",
                         reply_markup=keyboard())


@router.message(CreateDoseState.price)
async def price_input(message: Message, state: FSMContext):
    value = (message.text or "").strip().replace(' ', '').replace('\u00a0', '')
    if not value.isascii() or not value.isdecimal() or len(value) > 10 or not 0 < int(value) <= 1_000_000_000:
        await message.answer("Введіть додатну ціну в цілих гривнях, не більше 1 000 000 000.", reply_markup=keyboard())
        return
    await state.update_data(price=int(value))
    await state.set_state(CreateDoseState.confirm)
    data = await state.get_data()
    dose = f"{data['dose_value']:g}".replace('.', ',')
    await message.answer(
        "💉 <b>Перевірте нове дозування</b>\n\n"
        f"Препарат: <b>{escape(data['medication'])}</b>\n"
        f"Дозування: <b>{dose} мг</b>\n"
        f"Ціна за 1 тиждень: <b>{format_money(data['price'])} грн</b>",
        parse_mode="HTML", reply_markup=keyboard(confirm=True),
    )


@router.callback_query(F.data == "create_dose:confirm", CreateDoseState.confirm)
async def confirm_create_dose(query: CallbackQuery, state: FSMContext, services: Services):
    if not isinstance(query.message, Message):
        await query.answer()
        return
    data = await state.get_data()
    try:
        services.dose.create_dose(data['medication'], data['dose_value'], data['price'])
    except sqlite3.IntegrityError:
        await query.answer("Таке дозування вже існує. Новий запис не створено.", show_alert=True)
        return
    except ValueError as error:
        await query.answer(str(error), show_alert=True)
        return
    except sqlite3.Error:
        await query.answer("Не вдалося зберегти. Спробуйте ще раз.", show_alert=True)
        return
    await query.answer("Дозування створено")
    await show_doses(query, state, services, notice="✅ Дозування створено.\n\n")
