from dataclasses import asdict, is_dataclass
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.handlers.admin.panel import get_admin_main_menu_keyboard
from app.keyboards.admin_keyboards import build_patients_keyboard, get_user_cart_keyboard
from app.services.therapy_service import TherapyService
from app.services.user_service import UserService
from app.states.admin.AdminState import AdminState
from app.texts.admin import format_user_card
from app.container import Services

router = Router()


@router.message(F.text == "🔍 Знайти пацієнта", AdminState.show_admin_panel)
async def request_patient_data(message: Message, state: FSMContext):
    await state.set_state(AdminState.wait_patient_data)
    await message.answer("Введіть ФІО або номер телефону")


@router.message(AdminState.wait_patient_data)
async def process_patient_data(message: Message, state: FSMContext, services: Services):
    if message.text is None:
        return

    query = message.text
    users = services.user.search_users(query)

    if not users:
        await message.answer("Пацієнта не знайдено")
        return

    if len(users) == 1:
        user = users[0]
        await show_user_card(
            event=message,
            state=state,
            user=user,
            therapy_service=services.therapy
        )
        return

    await state.set_state(AdminState.wait_for_select_patient)
    await message.answer("Знайдено декылькох пацієнтів, оберіть потрібного",
                         reply_markup=build_patients_keyboard(users))

async def show_user_card(event: Message | CallbackQuery, user: dict, state: FSMContext, therapy_service: TherapyService):
    if is_dataclass(user):
        user = asdict(user)
    user_id = user["id"]
    active_therapy = therapy_service.get_active_therapy_by_user_id(user_id)
    planned_therapy = therapy_service.get_planned_therapy_by_user_id(user_id)

    user_card_text = format_user_card(
        user=user,
        planned_therapy=planned_therapy,
        active_therapy=active_therapy,
    )

    keyboard = get_user_cart_keyboard()

    await state.set_state(AdminState.show_patient)
    await state.update_data(user_id=user_id)


    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await event.message.edit_text(user_card_text, reply_markup=keyboard)
        return

    await event.answer(user_card_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("patient:"), AdminState.wait_for_select_patient)
async def select_patient(query: CallbackQuery, state: FSMContext, user_service : UserService, therapy_service : TherapyService):
    await query.answer()

    if query.data is None:
        return
    user_id = int(query.data.split(':',1)[1])

    user = user_service.get_by_user_id(user_id)

    if not user:
        return
    await show_user_card(
        event=query,
        state = state,
        user=user,
        therapy_service=therapy_service
        )


@router.callback_query(F.data == "admin_main_menu")
async def go_to_admin_panel(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await state.set_state(AdminState.show_admin_panel)

    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("Головне меню:")
    await query.message.answer("👨‍⚕️ ПАНЕЛЬ ЛІКАРЯ\n\nОберіть потрібний розділ:", reply_markup=get_admin_main_menu_keyboard())