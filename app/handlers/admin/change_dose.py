from datetime import date, datetime, timedelta
from html import escape
import sqlite3
import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.handlers.admin.user_card import show_user_card
from app.keyboards.admin_keyboards import build_doses_keyboard, get_confirm_change_dose_keyboard
from app.states.admin.AdminState import AdminState
from app.container import Services

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "change_dose", AdminState.show_patient)
@router.callback_query(F.data == "choose_another_dose", AdminState.wait_confirm_dose_change)
async def request_dose(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    doses = services.dose.get_all_doses() or []
    if not isinstance(query.message, Message):
        return
    if not doses:
        await query.message.answer("Доступних дозувань немає.")
        return
    await state.set_state(AdminState.change_dose)
    await query.message.edit_text("💉 Оберіть нове дозування:", reply_markup=build_doses_keyboard(doses))


@router.callback_query(F.data.startswith("dose_id:"), AdminState.change_dose)
async def process_dose(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await state.update_data(next_dose_id=int(query.data.split(":")[1]))
    await state.set_state(AdminState.select_date)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сьогодні", callback_data="date:today")],
        [InlineKeyboardButton(text="Завтра", callback_data="date:tomorrow")],
        [InlineKeyboardButton(text="Інша дата", callback_data="date:another")],
        [InlineKeyboardButton(text="Скасувати", callback_data="cancel_choose_dose")],
    ])
    await query.message.edit_text("Вкажіть дату початку терапії", reply_markup=keyboard)


async def show_confirmation(message: Message, state: FSMContext, services: Services, start_date: date):
    if start_date < date.today():
        await message.answer("Дата не може бути в минулому. Введіть дату у форматі ДД.ММ.РРРР.")
        return
    data = await state.get_data()
    user = services.user.get_by_user_id(data["user_id"])
    dose = services.dose.get_dose_by_dose_id(data["next_dose_id"])
    if user is None or dose is None:
        await message.answer("Пацієнта або дозування не знайдено. Поверніться до /admin.")
        return
    await state.update_data(start_date=start_date.isoformat())
    await state.set_state(AdminState.wait_confirm_dose_change)
    await message.answer(
        f"💉 Підтвердження призначення\n\nПацієнт: {escape(user.full_name)}\n"
        f"Препарат: {escape(dose.medication)}\nДозування: {dose.dose_value} мг\n"
        f"Початок: {start_date.strftime('%d.%m.%Y')}\n\n"
        "Нове призначення замінить попереднє заплановане. "
        "Поточна терапія завершиться в день початку нового призначення.",
        reply_markup=get_confirm_change_dose_keyboard(),
    )


@router.callback_query(F.data.startswith("date:"), AdminState.select_date)
async def select_date(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    choice = query.data.split(":")[1]
    if choice == "another":
        await state.set_state(AdminState.wait_write_date)
        await query.message.edit_text("Введіть дату початку у форматі ДД.ММ.РРРР, наприклад 15.10.2026.")
        return
    if choice not in {"today", "tomorrow"}:
        return
    await show_confirmation(query.message, state, services, date.today() + timedelta(days=choice == "tomorrow"))


@router.message(AdminState.wait_write_date)
async def process_date(message: Message, state: FSMContext, services: Services):
    try:
        start_date = datetime.strptime((message.text or "").strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Введіть дату у форматі ДД.ММ.РРРР, наприклад 15.10.2026.")
        return
    await show_confirmation(message, state, services, start_date)


@router.callback_query(F.data == "confirm_dose", AdminState.wait_confirm_dose_change)
async def confirm_dose(query: CallbackQuery, state: FSMContext, services: Services, bot: Bot):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    data = await state.get_data()
    user = services.user.get_by_user_id(data["user_id"])
    dose = services.dose.get_dose_by_dose_id(data["next_dose_id"])
    if user is None or dose is None:
        await query.message.answer("Пацієнта або дозування не знайдено. Поверніться до /admin.")
        return
    try:
        services.therapy.create_therapy(data["user_id"], data["next_dose_id"], date.fromisoformat(data["start_date"]))
    except ValueError as error:
        await query.message.answer(str(error))
        return
    except sqlite3.Error:
        await query.message.answer("Не вдалося зберегти призначення. Спробуйте ще раз.")
        return
    await state.set_state(AdminState.confirmed_dose)
    notification_status = "Пацієнту надіслано повідомлення."
    try:
        await bot.send_message(
            chat_id=user.tg_id,
            text=("💉 <b>Нове призначення від лікаря</b>\n\n"
                  f"Препарат: <b>{escape(dose.medication)}</b>\n"
                  f"Дозування: <b>{dose.dose_value:g} мг</b>\n"
                  f"Дата початку: <b>{date.fromisoformat(data['start_date']).strftime('%d.%m.%Y')}</b>\n\n"
                  "Деталі доступні в розділі «🌿 Моя терапія»"),
            parse_mode="HTML",
        )
    except TelegramAPIError:
        logger.exception("Could not deliver prescription notification to user %s", user.id)
        notification_status = "⚠️ Не вдалося повідомити пацієнта. Призначення збережено; зв’яжіться з пацієнтом окремо."
    await query.message.edit_text("✅ Призначення збережено\n\n" + notification_status, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Карта пацієнта", callback_data="card_of_patient")],
        [InlineKeyboardButton(text="Панель лікаря", callback_data="admin_main_menu")],
    ]))


@router.callback_query(F.data == "cancel_choose_dose", StateFilter(
    AdminState.change_dose, AdminState.select_date,
    AdminState.wait_write_date, AdminState.wait_confirm_dose_change,
))
@router.callback_query(F.data == "card_of_patient", AdminState.confirmed_dose)
async def card_of_patient(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    data = await state.get_data()
    if not data.get("user_id"):
        return
    user = services.user.get_by_user_id(data["user_id"])
    if user:
        await show_user_card(query, user, state, services.therapy)
