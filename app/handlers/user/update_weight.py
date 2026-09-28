from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.utils.validators import *
from app.states.user.update_weight import UpdateWeightState
from app.database.repositories.user_repository import user_repository
from app.database.repositories.weight_repository import weight_repository


# ===================================================KEYBOARDS===================================================

def get_show_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")]
        ]
    )


def get_confirm_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm_weight")],
        [InlineKeyboardButton(text="✏️ Ввести ще раз", callback_data="repeat_weight")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel:update_weight")]
        ]
    )


def get_cancel_update_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel:update_weight")]
    ])

# ==============================================================================================================

router = Router()


@router.message(StateFilter(None),  F.text == "⚖️ Оновити вагу")
async def show_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateWeightState.show_weight)
    await message.answer("⏰ Час оновити вагу\n\n"
                "Зважтеся вранці натщесерце та внесіть актуальний показник у бот.", reply_markup=get_show_weight_keyboard())


@router.callback_query(F.data == "update_weight", UpdateWeightState.show_weight)
async def request_weight(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    user = user_repository.get_by_tg_id(tg_id=query.from_user.id)
    current_weight = user["current_weight"]
    text = (
        "⚖️ <b>Оновлення ваги</b>\n\n"
        f"Ваша актуальна вага: {current_weight} кг\n"
        "Введіть нову вагу в кілограмах одним повідомленням.\n"
        "Наприклад: 83.7\n\n"
        "Для точнішого відстеження рекомендуємо зважуватися вранці, "
        "натщесерце та приблизно в однакових умовах."
    )

    await state.set_state(UpdateWeightState.wait_for_weight)
    await state.update_data(message_id=query.message.message_id)
    await query.message.edit_text(text, reply_markup=get_cancel_update_weight_keyboard())


@router.message(UpdateWeightState.wait_for_weight)
async def process_weight(message: Message, state: FSMContext, bot: Bot):
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

    data = await state.get_data()
    message_id = data.get('message_id')

    if message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message_id,
            reply_markup=None,
        )

    new_weight = float(new_weight_str)

    await state.update_data(new_weight=new_weight)

    tg_id = message.from_user.id
    user = user_repository.get_by_tg_id(tg_id)

    last_weight = user['current_weight']

    await state.set_state(UpdateWeightState.confirm_weight)
    await message.answer(
        "⚖️ <b>Підтвердіть нову вагу</b>\n\n"
            f"Попередня вага: {last_weight} кг\n"
            f"Нова вага: {new_weight} кг\n"
            f"Зміна: {round(new_weight - last_weight,1)} кг\n"
            "Усе правильно?", reply_markup=get_confirm_weight_keyboard()
    )


@router.callback_query(F.data == "repeat_weight")
async def repeat_weight(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await request_weight(query, state=state)


@router.callback_query(F.data == "confirm_weight")
async def confirm(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    tg_id = query.from_user.id

    data = await state.get_data()
    user = user_repository.get_by_tg_id(tg_id)

    start_weight = user["start_weight"]
    current_weight = data['new_weight']

    weight_id = weight_repository.update_by_tg_id(tg_id=tg_id, new_weight=current_weight)
    rowcount = user_repository.update_current_weight_by_tg_id(tg_id=tg_id, current_weight=current_weight)
    if not weight_id or not rowcount:
        await query.message.answer("Не вдалося оновити вагу, повторіть спробу пізніше")
        return

    await query.message.edit_text(
        "✅ Вагу успішно оновлено!\n\n"
        f"Початкова вага: {start_weight} кг\n"
        f"Актуальна вага: {current_weight} кг\n"
        f"Загальний результат: {round(current_weight - start_weight,1)} кг\n\n"
        f"Продовжуйте рухатися до своєї мети поступово та дотримуйтеся рекомендацій лікаря 🌿",
    )

    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "cancel:update_weight")
async def cancel_update_weight(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("❌ Оновлення ваги скасовано")
    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()