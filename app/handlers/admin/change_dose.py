from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.service import get_doses, get_dose_by_id

from app.handlers.admin.find_patient import show_patient
from app.handlers.admin.panel import show_admin_panel

from app.states.admin.AdminState import AdminState

router = Router()

@router.callback_query(F.data == "change_dose", AdminState.show_patient)
async def change_dose(query: CallbackQuery , state: FSMContext):
    doses = get_doses()

    data = await state.get_data()
    active_dose = data["active_dose"]

    builder = InlineKeyboardBuilder()

    for dose in doses:
        builder.add(InlineKeyboardButton(text=f"{dose["medication"]} - {dose["dose_value"]}",
                                         callback_data=f"dose_id:{dose["id"]}"))

    builder.adjust(1)
    inline_keyboard = builder.as_markup()
    text = ("💉 Зміна дозування\n\n"
            "Поточне дозування пацієнта:\n"
            f"💊 {active_dose["medication"]} 💉 {active_dose["dose_value"]} мг  \n\n"
            "Оберіть нове дозування зі списку нижче.")

    await query.answer()
    await state.set_state(AdminState.change_dose)
    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data.startswith("dose_id:"), AdminState.change_dose)
async def confirm_dose_change(query: CallbackQuery, state: FSMContext):
    if query.data is None:
        return

    dose_id = int(query.data.split(":")[1])
    next_dose = get_dose_by_id(dose_id)

    await state.update_data(
        next_dose=next_dose
    )

    data = await state.get_data()
    patient = data["patient"]
    active_dose = data["active_dose"]

    if patient is None:
        await query.answer("Пацієнта не знайдено")
        return

    if active_dose is None:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {patient["full_name"]}\n"
        )
    else:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {patient["full_name"]}\n"
            f"Препарат: {active_dose["medication"]}\n"
            f"Поточне дозування: {active_dose["dose_value"]} мг\n"
            f"Препарат: {next_dose["medication"]}\n"
            f"Нове дозування: {next_dose["dose_value"]} мг\n\n"
            "Перевірте дані перед підтвердженням. Після"
            " підтвердження нове дозування буде збережено як актуальне призначення пацієнта."
        )


    if not isinstance(query.message, Message):
        return

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard= [
            [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_dose")],
            [InlineKeyboardButton(text="⬅️ Обрати інше", callback_data="choose_another_dose")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_choose_dose")]
        ]
    )
    await state.set_state(AdminState.wait_confirm_dose_change)
    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data == "confirm_dose", AdminState.wait_confirm_dose_change)
async def confirm_dose(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    patient = data["patient"]
    next_dose = data["next_dose"]

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard= [
            [InlineKeyboardButton(text="👤 Карта пацієнта", callback_data="card_of_patient")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main_menu")],
        ]
    )
    text = (
        "✅ Дозування успішно оновлено\n\n"
        f"👤 Пацієнт: {patient['full_name']}\n"
        f"💊 Препарат: {next_dose['medication']}\n"
        f"💉 Нове дозування: {next_dose["dose_value"]} мг"
    )
    await state.set_state(AdminState.confirmed_dose)
    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data == "choose_another_dose", AdminState.wait_confirm_dose_change)
async def choose_another_dose(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await change_dose(query=query, state=state)


@router.callback_query(F.data == "cancel_choose_dose", AdminState.wait_confirm_dose_change)
async def cancel_choose_dose(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.answer()
    await query.message.edit_text("❌ Зміну дозування відмінено")
    await show_patient(query.message, state=state)

@router.callback_query(F.data == "card_of_patient")
async def card_of_patient(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await state.update_data(message_id = query.message.message_id)
    await query.answer()
    await query.message.edit_reply_markup(
        reply_markup=None
    )

    await show_patient(query.message, state)


@router.callback_query(F.data == "back_to_main_menu", AdminState.confirmed_dose)
async def back_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.answer()
    await query.message.edit_text("Головне меню:")
    await state.clear()
    await show_admin_panel(message=query.message, state=state)