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
        [InlineKeyboardButton(text="🔄 Змінити вагу", callback_data="repeat_weight")],
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:update_weight")]
        ]
    )


def get_cancel_update_weight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:update_weight")]
    ])

# ==============================================================================================================

router = Router()


@router.message(StateFilter(None),  F.text == "⚖️ Оновити вагу")
async def show_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateWeightState.show_weight)
    await message.answer("⚖️<b> Час оновити вагу</b>\n\n"
                         "Будь ласка, зважтеся вранці натщесерце та внесіть актуальну вагу в бот.\n\n"
                         "Якщо маєте можливість, також радимо додати актуальні заміри тіла — це допоможе точніше оцінювати зміни та ваш прогрес за цей тиждень.\n\n"
                         "Регулярні вимірювання допомагають нам уважно стежити за динамікою протягом терапії.\n\n"
                         "<i>Дякуємо, що дбаєте про себе разом з Elvia </i>🤍", reply_markup=get_show_weight_keyboard())


@router.callback_query(F.data == "update_weight", UpdateWeightState.show_weight)
async def request_weight(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    user = user_repository.get_by_tg_id(tg_id=query.from_user.id)
    current_weight = user["current_weight"]
    text = ("⚖️ <b>Оновлення ваги</b>\n\n"
            f"Ваша поточна вага — <b>{current_weight} кг</b>\n\n"
            "Введіть нове значення ваги одним повідомленням у кілограмах.\n"
            "Наприклад: <i>83.7</i>\n\n"
            "Для точного відстеження прогресу рекомендуємо зважуватися вранці натщесерце та, за можливості, в однакових умовах.\n\n"
            "<i>Кожне оновлення допомагає краще бачити динаміку ваших результатів</i> 🤍")

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

    text = (
        "⚖️ <b>Підтвердження ваги</b>\n\n"
        "Перевірте, будь ласка, чи правильно вказані дані:\n\n"
        f"Попередня вага — <b>{last_weight} кг</b>\n"
        f"Нова вага — <b>{new_weight} кг</b>\n\n"
        f"Різниця: <b>{round(new_weight - last_weight, 1)} кг</b>\n\n"
        "<i>Якщо все правильно, підтвердьте оновлення нижче</i> 🤍"
    )

    await state.set_state(UpdateWeightState.confirm_weight)
    await message.answer(text, reply_markup=get_confirm_weight_keyboard())


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

    text = ("✅<b>Вагу успішно оновлено!</b>\n\n"
            f"Початкова вага — <b>{start_weight} кг</b>\n"
            f"Поточна вага — <b>{current_weight} кг</b>\n"
            f"Зміна від початку: <b>{round(current_weight - start_weight,1)} кг</b>\n\n"
            "<i>Продовжуйте дотримуватися рекомендацій лікаря та регулярно оновлювати свої показники</i> 🌿")
    await query.message.edit_text(text)

    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "cancel:update_weight")
async def cancel_update_weight(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_text("❌ Оновлення ваги скасовано")
    await query.message.answer("Головне меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()