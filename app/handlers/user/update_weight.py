from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.utils.validators import *
from app.states.user.update_weight import UpdateWeightState
from container import Services
from keyboards.user import get_show_weight_keyboard, get_cancel_update_weight_keyboard, get_confirm_weight_keyboard
from texts.user import START_UPDATE_WEIGHT_TEXT, format_request_weight, format_confirm_weight, \
    format_success_change_weight

router = Router()


@router.message(StateFilter(None),  F.text == "⚖️ Оновити вагу")
async def show_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateWeightState.show_weight)
    await message.answer(START_UPDATE_WEIGHT_TEXT, reply_markup=get_show_weight_keyboard())


@router.callback_query(F.data == "update_weight", UpdateWeightState.show_weight)
async def request_weight(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    tg_id = query.from_user.id

    user = services.user.get_user_by_tg_id(tg_id)
    if user is None:
        return

    await state.set_state(UpdateWeightState.wait_for_weight)
    await state.update_data(message_id=query.message.message_id)
    await query.message.edit_text(format_request_weight(user), reply_markup=get_cancel_update_weight_keyboard())


@router.message(UpdateWeightState.wait_for_weight)
async def process_weight(message: Message, state: FSMContext, bot: Bot, services: Services):
    if message.text is None:
        return
    if message.from_user is None:
        return

    new_weight_str = message.text.replace(",", ".")
    if not is_valid_weight(new_weight_str):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n Наприклад: <i>84.3</i>"
        )
        return
    new_weight = float(new_weight_str)

    await state.update_data(new_weight=new_weight)

    data = await state.get_data()
    message_id = data.get('message_id')
    if message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message_id,
            reply_markup=None,
        )
    await show_confirm_weight(
        message=message,
        state=state,
        services=services
    )

async def show_confirm_weight(message: Message, state: FSMContext, services: Services):
    if message.from_user is None:
        return
    tg_id = message.from_user.id

    user = services.user.get_user_by_tg_id(tg_id)
    if user is None:
        return

    data = await state.get_data()
    new_weight = data.get('new_weight')
    if not isinstance(new_weight, float):
        return

    await state.set_state(UpdateWeightState.confirm_weight)
    await message.answer(format_confirm_weight(last_weight=user.current_weight, new_weight=new_weight), reply_markup=get_confirm_weight_keyboard())


@router.callback_query(F.data == "repeat_weight")
async def repeat_weight(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    await request_weight(query, state=state, services=services)


@router.callback_query(F.data == "confirm_weight")
async def confirm_weight(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    tg_id = query.from_user.id

    patient = services.user.get_user_by_tg_id(tg_id)
    if patient is None:
        return

    data = await state.get_data()
    new_weight = data.get('new_weight')
    if not isinstance(new_weight, float):
        return

    last_weight = patient.current_weight

    weight_id = services.weight.add_weight_by_user_id(user_id=patient.id, weight=new_weight)
    rowcount = services.user.update_current_weight_by_user_id(user_id=patient.id, new_weight=new_weight)

    if not weight_id or not rowcount:
        await query.message.answer("Не вдалося оновити вагу, повторіть спробу пізніше")
        return

    await query.message.edit_text(format_success_change_weight(last_weight, new_weight))
    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "cancel:update_weight")
async def cancel_update_weight(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("❌ Оновлення ваги скасовано")
    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()