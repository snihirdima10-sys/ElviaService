import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery

from app.handlers.admin.panel import show_admin_panel
from app.handlers.admin.user_card import show_user_card
from app.keyboards.admin_keyboards import build_doses_keyboard, get_confirm_change_dose_keyboard
from app.services.dose_service import DoseService
from app.services.therapy_service import TherapyService
from app.services.user_service import UserService
from app.states.admin.AdminState import AdminState


router = Router()


@router.callback_query(F.data == "change_dose", AdminState.show_patient)
async def request_dose(query: CallbackQuery , state: FSMContext, therapy_service: TherapyService, dose_service: DoseService):
    await query.answer()
    data = await state.get_data()

    user_id = data["user_id"]

    doses = dose_service.get_all_doses()
    active_therapy = therapy_service.get_active_therapy_by_user_id(user_id)
    if active_therapy is None:
        text = ("💉 Зміна дозування\n\n"
                "Поточне дозування немає:\n"
                "Оберіть нове дозування зі списку нижче.")
    else:
        text = ("💉 Зміна дозування\n\n"
                "Поточне дозування пацієнта:\n"
                f"💊 {active_therapy["medication"]} 💉 {active_therapy["dose_value"]} мг  \n\n"
                "Оберіть нове дозування зі списку нижче.")

    if isinstance(query.message, Message):
        await state.set_state(AdminState.change_dose)
        await query.message.edit_text(text, reply_markup=build_doses_keyboard(doses))


class InlineKeyboardMarku:
    pass


@router.callback_query(F.data.startswith("dose_id:"), AdminState.change_dose)
async def process_dose(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if query.data is None:
        return
    next_dose_id = int(query.data.split(":")[1])
    await state.update_data(next_dose_id=next_dose_id)

    select_date = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сьогодні", callback_data="date:today")],
            [InlineKeyboardButton(text="Завтра", callback_data="date:tomorrow")],
            [InlineKeyboardButton(text="Інша дата", callback_data="date:another")]

        ]
    )

    if isinstance(query.message, Message):
        await state.set_state(AdminState.select_date)
        await query.message.edit_text("Вкажіть дату початку терапії", reply_markup=select_date)


@router.callback_query(F.data.startswith("date:"), AdminState.select_date)
async def process_date(query: CallbackQuery, state: FSMContext, user_service: UserService, therapy_service: TherapyService,  dose_service: DoseService):
    if query.data is None:
        return
    start_date = query.data.split(':', 1)[1]

    if start_date == "today":
        start_date = (datetime.date.today())
    if start_date == "tomorrow":
        start_date = (datetime.date.today() + datetime.timedelta(days=1))
    if start_date == "another":
        await state.set_state(AdminState.wait_write_date)
        await query.message.edit_text("Вкажіть дату початку терапії в форматі d.m.Y")
        return

    data = await state.get_data()

    user_id = data["user_id"]
    next_dose_id = data["next_dose_id"]

    user = user_service.get_by_user_id(user_id)
    active_therapy = therapy_service.get_active_therapy_by_user_id(user_id)

    next_dose = dose_service.get_dose_by_dose_id(next_dose_id)

    await state.update_data(
        next_dose_id=next_dose_id,
        start_date=start_date
    )

    if user is None:
        await query.message.answer("Пацієнта не знайдено")
        return

    if active_therapy is None:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {user["full_name"]}\n"
            f"Препарат: {next_dose["medication"]}\n"
            f"Нове дозування: {next_dose["dose_value"]} мг\n\n"
            f"початок з: {start_date}"
        )
    else:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {user["full_name"]}\n"
            f"Препарат: {active_therapy["medication"]}\n"
            f"Поточне дозування: {active_therapy["dose_value"]} мг\n"
            f"Препарат: {next_dose["medication"]}\n"
            f"Нове дозування: {next_dose["dose_value"]} мг\n\n"
            f"початок з: {start_date}"
            "Перевірте дані перед підтвердженням. Після"
            " підтвердження нове дозування буде збережено як актуальне призначення пацієнта."
        )

    await state.set_state(AdminState.wait_confirm_dose_change)

    await query.message.answer(text, reply_markup=get_confirm_change_dose_keyboard())




@router.message(AdminState.wait_write_date)
async def process_date(message: Message, state: FSMContext, user_service: UserService, therapy_service: TherapyService, dose_service: DoseService):
    if message.text is None:
        return

    try:
        start_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Введыть коректну дату")
        return

    data = await state.get_data()

    user_id = data["user_id"]
    next_dose_id = data["next_dose_id"]


    user = user_service.get_by_user_id(user_id)
    active_therapy = therapy_service.get_active_therapy_by_user_id(user_id)

    next_dose = dose_service.get_dose_by_dose_id(next_dose_id)


    await state.update_data(
        next_dose_id=next_dose_id,
        start_date=start_date
    )

    if user is None:
        await message.answer("Пацієнта не знайдено")
        return

    if active_therapy is None:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {user["full_name"]}\n"
            f"Препарат: {next_dose["medication"]}\n"
            f"Нове дозування: {next_dose["dose_value"]} мг\n\n"
            f"початок з: {start_date}"
        )
    else:
        text = (
            "💉 Підтвердження зміни дозування\n\n"
            f"Пацієнт: {user["full_name"]}\n"
            f"Препарат: {active_therapy["medication"]}\n"
            f"Поточне дозування: {active_therapy["dose_value"]} мг\n"
            f"Препарат: {next_dose["medication"]}\n"
            f"Нове дозування: {next_dose["dose_value"]} мг\n\n"
            f"початок з: {start_date}"
            "Перевірте дані перед підтвердженням. Після"
            " підтвердження нове дозування буде збережено як актуальне призначення пацієнта."
        )

    await state.set_state(AdminState.wait_confirm_dose_change)

    await message.answer(text, reply_markup=get_confirm_change_dose_keyboard())


@router.callback_query(F.data == "confirm_dose", AdminState.wait_confirm_dose_change)
async def confirm_dose(query: CallbackQuery, state: FSMContext, user_service: UserService, therapy_service: TherapyService, dose_service: DoseService):
    data = await state.get_data()
    user_id = data["user_id"]
    next_dose_id = data["next_dose_id"]
    start_date = data["start_date"]

    user = user_service.get_by_user_id(user_id)
    next_dose = dose_service.get_dose_by_dose_id(next_dose_id)
    if user is None:
        return
    try:
        therapy_id = therapy_service.create_therapy(user_id, next_dose_id, start_date)
        if therapy_id:
            text = (
                "✅ Дозування успішно оновлено\n\n"
                f"👤 Пацієнт: {user['full_name']}\n"
                f"💊 Препарат: {next_dose['medication']}\n"
                f"💉 Нове дозування: {next_dose["dose_value"]} мг"
            )
        else:
            text = "Щось пішло не так"

    except Exception:
        raise


    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard= [
            [InlineKeyboardButton(text="👤 Карта пацієнта", callback_data="card_of_patient")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="back_to_main_menu")],
        ]
    )

    if isinstance(query.message, Message):
        await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data == "choose_another_dose", AdminState.wait_confirm_dose_change)
async def choose_another_dose(query: CallbackQuery, state: FSMContext, dose_service: DoseService, therapy_service: TherapyService):
    await query.answer()
    await request_dose(query=query, state=state, dose_service=dose_service, therapy_service=therapy_service)


@router.callback_query(F.data == "cancel_choose_dose", AdminState.wait_confirm_dose_change)
async def cancel_choose_dose(query: CallbackQuery, state: FSMContext, user_service: UserService, therapy_service: TherapyService):
    await query.answer()
    data = await state.get_data()
    user = user_service.get_by_user_id(data["user_id"])

    if isinstance(query.message, Message):
        if user:
            await query.message.edit_text("❌ Зміну дозування відмінено")
            await show_user_card(
                event=query,
                user=user,
                state=state,
                therapy_service=therapy_service
                )

@router.callback_query(F.data == "card_of_patient")
async def card_of_patient(query: CallbackQuery, state: FSMContext, therapy_service: TherapyService, user_service: UserService):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await state.update_data(message_id = query.message.message_id)
    await query.answer()
    await query.message.edit_reply_markup(
        reply_markup=None
    )
    data = await state.get_data()
    user_id = data["user_id"]
    user = user_service.get_by_user_id(user_id)
    if user:
        await show_user_card(event=query, user=user, state=state, therapy_service=therapy_service)


@router.callback_query(F.data == "back_to_main_menu", AdminState.confirmed_dose)
async def back_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.answer()
    await query.message.edit_text("Головне меню:")
    await state.clear()
    await show_admin_panel(message=query.message, state=state)