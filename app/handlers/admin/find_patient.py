from aiogram import F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.service import find_users, get_active_dose_by_user_id, get_user_by_id
from app.handlers.admin.panel import show_admin_panel

from app.states.admin.AdminState import AdminState

router = Router()

async def show_patient(message: Message, state: FSMContext):
    data = await state.get_data()
    patient = data["patient"]
    active_dose = data["active_dose"]
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💉 Змінити дозування", callback_data="change_dose")],
            [InlineKeyboardButton(text="📋 Історія терапії", callback_data="therapy_history")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main_menu")]
        ]
    )

    text = (
        "👤 КАРТА ПАЦІЄНТА\n\n"
        f"👤 {patient["full_name"]}\n"
        f"📱 Телефон: {patient["phone"]}\n"
        f"📅 Реєстрація: {patient["created_at"]}\n"
        f"📏 Зріст: {patient["height"]} см\n"
        f"⚖️ Початкова вага: {patient["start_weight"]} кг\n"
        f"⚖️ Актуальна вага: {patient["current_weight"]} кг\n"
        f"📉 Результат: {round(patient["current_weight"] - patient["start_weight"], 1)}кг\n\n"
        "💉 ПОТОЧНА ТЕРАПІЯ\n\n"
        f"💊 Препарат: {active_dose["medication"]}\n"
        f"💉 Дозування: {active_dose["dose_value"]} мг\n"
        f"📅 Початок: {active_dose["start_date"]}\n"
    )

    await state.set_state(AdminState.show_patient)

    if data.get("message_id"):
        await message.edit_text(text, reply_markup=inline_keyboard)
        await state.update_data(message_id=None)
    else:

        await message.answer(text, reply_markup=inline_keyboard)

@router.message(F.text == "🔍 Знайти пацієнта", AdminState.show_admin_panel)
async def wait_patient_data(message: Message, state: FSMContext):
    await state.set_state(AdminState.wait_patient_data)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Скасувати")]
        ], resize_keyboard=True
    )


    await message.answer(
        "🔍 Пошук пацієнта\n\n"
        "Введіть ім’я та прізвище пацієнта або його номер телефону.",
        reply_markup=keyboard
    )

@router.message(F.text != "❌ Скасувати", AdminState.wait_patient_data)
async def finding_patient(message: Message, state: FSMContext):
    if message.text is None:
        return

    patients = find_users(message.text)

    if not patients:
        await message.answer("❌ Пацієнта не знайдено.")
        return

    if len(patients) == 1:
        patient = patients[0]
        await save_and_show_patient(message, state, patient)
        return

    builder = InlineKeyboardBuilder()

    for patient in patients:
        builder.add(
            InlineKeyboardButton(
                text=f"{patient['full_name']} • {patient['phone']}",
                callback_data=f"select_patient:{patient['id']}"
            )
        )

    builder.adjust(1)

    await message.answer(
        "🔍 Знайдено декілька пацієнтів.\n\nОберіть потрібного:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("select_patient:"))
async def select_patient(query: CallbackQuery, state: FSMContext):
    await query.answer()

    if query.data is None or not isinstance(query.message, Message):
        return

    try:
        patient_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("Некоректний ID пацієнта", show_alert=True)
        return

    patient = get_user_by_id(patient_id)

    if patient is None:
        await query.answer("Пацієнта не знайдено", show_alert=True)
        return

    active_dose = get_active_dose_by_user_id(patient["tg_id"])

    await state.update_data(patient=patient, active_dose=active_dose)

    await state.set_state(AdminState.show_patient)

    await show_patient(query.message, state)

async def save_and_show_patient(message: Message, state: FSMContext, patient: dict):
    active_dose = get_active_dose_by_user_id(patient["tg_id"])

    await state.update_data(patient=patient, active_dose=active_dose)

    await state.set_state(AdminState.show_patient)

    await show_patient(message, state)


@router.message(F.text == "❌ Скасувати", AdminState.wait_patient_data)
async def cancel_finding_patient(message: Message, state: FSMContext):
    await message.answer("❌ Пошук скасований.")
    await state.clear()
    await show_admin_panel(message=message, state=state)


@router.callback_query(F.data == "back_to_main_menu", AdminState.show_patient)
async def back_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("Головне меню:")
    await state.clear()
    await show_admin_panel(message=query.message, state=state)
