import sqlite3
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.container import Services
from app.utils.formatter import format_money

router = Router()
PAGE_SIZE = 10


class DeleteDoseState(StatesGroup):
    select = State()
    confirm = State()


async def show_doses(event: Message | CallbackQuery, state: FSMContext, services: Services, page=0, notice=""):
    doses = services.dose.get_all_doses() or []
    page = min(max(0, page), max(0, (len(doses) - 1) // PAGE_SIZE))
    await state.clear()
    await state.set_state(DeleteDoseState.select)
    await state.update_data(dose_page=page)
    rows = [[InlineKeyboardButton(
        text=f"{dose['medication']} · {dose['dose_value']:g} мг · {format_money(dose['price'])} грн",
        callback_data=f"delete_dose:select:{dose['id']}",
    )] for dose in doses[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]]
    navigation = []
    if page:
        navigation.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delete_dose:page:{page - 1}"))
    if (page + 1) * PAGE_SIZE < len(doses):
        navigation.append(InlineKeyboardButton(text="Далі ➡️", callback_data=f"delete_dose:page:{page + 1}"))
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text="➕ Додати", callback_data="create_dose:start")])
    rows.append([InlineKeyboardButton(text="🏠 Панель лікаря", callback_data="admin_main_menu")])
    text = notice + "💉 <b>Дозування</b>\n\n"
    text += (f"Оберіть дозування для видалення або додайте нове.\n\nСторінка {page + 1} з {(len(doses) + PAGE_SIZE - 1) // PAGE_SIZE}."
             if doses else "Доступних дозувань немає.")
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=markup)


@router.message(F.text == "💉 Дозування")
async def open_doses(message: Message, state: FSMContext, services: Services):
    await show_doses(message, state, services)


@router.callback_query(F.data.startswith("delete_dose:page:"))
async def dose_page(query: CallbackQuery, state: FSMContext, services: Services):
    value = query.data.rsplit(':', 1)[1]
    if not value.isdecimal():
        await query.answer("Некоректна сторінка")
        return
    await query.answer()
    await show_doses(query, state, services, int(value))


@router.callback_query(F.data.startswith("delete_dose:select:"), DeleteDoseState.select)
async def select_dose(query: CallbackQuery, state: FSMContext, services: Services):
    value = query.data.rsplit(':', 1)[1]
    dose = services.dose.get_active_dose(int(value)) if value.isdecimal() else None
    if dose is None:
        await query.answer("Це дозування вже видалено або не знайдено.", show_alert=True)
        return
    if not isinstance(query.message, Message):
        await query.answer()
        return
    data = await state.get_data()
    await state.update_data(delete_dose_id=dose.id)
    await state.set_state(DeleteDoseState.confirm)
    await query.answer()
    await query.message.edit_text(
        "🗑 <b>Видалити дозування?</b>\n\n"
        f"Препарат: <b>{escape(dose.medication)}</b>\n"
        f"Дозування: <b>{dose.dose_value:g} мг</b>\n"
        f"Ціна за тиждень: <b>{format_money(dose.price)} грн</b>\n\n"
        "Воно зникне зі списку для нових призначень. Наявна терапія та замовлення збережуться.",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Так, видалити", callback_data=f"delete_dose:confirm:{dose.id}")],
            [InlineKeyboardButton(text="⬅️ До списку", callback_data=f"delete_dose:page:{data.get('dose_page', 0)}")],
            [InlineKeyboardButton(text="🏠 Панель лікаря", callback_data="admin_main_menu")],
        ]),
    )


@router.callback_query(F.data.startswith("delete_dose:confirm:"), DeleteDoseState.confirm)
async def confirm_delete(query: CallbackQuery, state: FSMContext, services: Services):
    data = await state.get_data()
    value = query.data.rsplit(':', 1)[1]
    if not value.isdecimal() or int(value) != data.get('delete_dose_id'):
        await query.answer("Оберіть дозування зі списку ще раз.", show_alert=True)
        return
    try:
        deleted = services.dose.delete_dose(int(value))
    except sqlite3.Error:
        await query.answer("Не вдалося видалити. Спробуйте ще раз.", show_alert=True)
        return
    await query.answer("Дозування видалено" if deleted else "Дозування вже видалено")
    await show_doses(query, state, services, data.get('dose_page', 0), "✅ Дозування видалено зі списку.\n\n")
