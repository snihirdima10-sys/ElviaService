from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from app.database.service import get_user_dose_history
from app.handlers.admin.panel import show_admin_panel
from app.states.admin.AdminState import AdminState

router = Router()


@router.callback_query(F.data == "therapy_history")
async def show_therapy_history(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    patient = data["patient"]
    doses = get_user_dose_history(patient["tg_id"])
    text = ""

    for dose in doses:
        text += (f"💉 {dose["medication"]} · {dose["dose_value"]} мг\n"
                 f"{dose["start_date"]}–{dose["end_date"]} · 4 тижні\n"
                 f"Вага: 92 → 89,2 кг\n"
                 f"Результат: −2,8 кг\n\n")

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Карта пацієнта", callback_data="card_of_patient")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main_menu")],
        ]
    )
    await state.set_state(AdminState.show_therapy_history)
    await query.message.edit_text(
        "📋 ІСТОРІЯ ТЕРАПІЇ\n\n"
        f"👤 {patient["full_name"]}\n\n" 
        f"Початкова вага: {patient["start_weight"]} кг\n"
        f"Поточна вага: {patient["current_weight"]} кг\n"
        f"Загальний результат: {round(patient["current_weight"] - patient["start_weight"],1)} кг\n\n"
        + text, reply_markup=inline_keyboard
    )


@router.callback_query(F.data == "back_to_main_menu", AdminState.show_therapy_history)
async def back_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("Головне меню:")
    await state.clear()
    await show_admin_panel(message=query.message, state=state)