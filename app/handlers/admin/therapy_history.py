from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.handlers.admin.panel import show_admin_panel
from app.handlers.admin.user_card import show_user_card
from app.keyboards.admin_keyboards import get_therapy_history_keyboard
from app.states.admin.AdminState import AdminState
from app.texts.admin import format_therapies_history

from app.services.user_service import UserService
from app.services.therapy_service import TherapyService



router = Router()


@router.callback_query(F.data == "therapy_history")
async def show_therapy_history(query: CallbackQuery, state: FSMContext, user_service: UserService, therapy_service: TherapyService):
    data = await state.get_data()
    user_id = data["user_id"]
    user = user_service.get_by_user_id(user_id)

    active_therapy = therapy_service.get_active_therapy_by_user_id(user_id)
    therapies_history = therapy_service.get_history_therapy_by_user_id(user_id)

    await state.set_state(AdminState.show_therapy_history)

    if isinstance(query.message, Message):
        if user is not None:
            await query.message.edit_text(format_therapies_history(
                user=user,
                active_therapy=active_therapy,
                therapies_history=therapies_history
                ),
            reply_markup=get_therapy_history_keyboard()
            )


@router.callback_query(F.data == "back_to_main_menu", AdminState.show_therapy_history)
async def back_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("Головне меню:")
    await state.clear()
    await show_admin_panel(message=query.message, state=state)

@router.callback_query(F.data == "show_card_of_patient", AdminState.show_therapy_history)
async def show_card_of_patient(query: CallbackQuery, state: FSMContext, user_service: UserService, therapy_service: TherapyService):
    await query.answer()
    data = await state.get_data()
    user = user_service.get_by_user_id(data["user_id"])
    if user:
        await show_user_card(
            event=query,
            user=user,
            state=state,
            therapy_service=therapy_service

        )