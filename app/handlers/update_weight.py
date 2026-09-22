from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup,InlineKeyboardButton, Message, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.main_menu import main_menu
from app.utils.validators import validate_weight
from app.database.service import get_user_by_id, update_weight


class UpdateState(StatesGroup):
    wait_for_weight = State()
    check_weight = State()


router = Router()

text = (
    "⚖️ Оновлення ваги\n\n"
    "Ваша актуальна вага: 84,3 кг\n"
    "Введіть нову вагу в кілограмах одним повідомленням.\n"
    "Наприклад: 83.7\n\n"
    "Для точнішого відстеження рекомендуємо зважуватися вранці, "
    "натщесерце та приблизно в однакових умовах."
    )

@router.callback_query(F.data == "update_weight")
async def process_weight(query: CallbackQuery, state: FSMContext):
    await state.set_state(UpdateState.wait_for_weight)

    if not isinstance(query.message, Message):
        return
    await query.message.edit_text(
        text
    )


@router.message(F.text == "⚖️ Оновити вагу")
async def get_weight(message: Message, state: FSMContext):
    await state.set_state(UpdateState.wait_for_weight)
    await message.answer(text, reply_markup=ReplyKeyboardRemove())



@router.message(UpdateState.wait_for_weight)
async def process_weight(message: Message, state: FSMContext):

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm")],
        [InlineKeyboardButton(text="✏️ Ввести ще раз", callback_data="repeat")]
    ])

    if message.text is None:
        return

    if not validate_weight(message.text):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n"
            "Наприклад: 84.3"
        )
        return

    current_weight = message.text.replace(",", ".")
    await state.update_data(current_weight=current_weight)

    if message.from_user is None:
        return
    tg_id = message.from_user.id
    data = get_user_by_id(tg_id)

    previous_weight = data['current_weight']
    result_weight = round(float(current_weight) - float(previous_weight),1)

    await state.set_state(UpdateState.check_weight)
    await message.answer(
        "⚖️ Підтвердіть нову вагу\n\n"
            f"Попередня вага: {previous_weight} кг\n"
            f"Нова вага: {current_weight} кг\n"
            f"Зміна: {result_weight} кг\n"
            "Усе правильно?", reply_markup=inline_keyboard
    )


@router.callback_query(F.data == "repeat")
async def repeat(query: CallbackQuery, state: FSMContext):

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Оновити вагу", callback_data="update_weight")],
    ])

    if not isinstance(query.message, Message):
        return

    await query.message.edit_text("⏰ Час оновити вагу\n\n"
                "Зважтеся вранці натщесерце та внесіть актуальний показник у бот.", reply_markup=inline_keyboard)


@router.callback_query(F.data == "confirm")
async def confirm(query: CallbackQuery, state: FSMContext):
    tg_id = int(query.from_user.id)

    data = await state.get_data()

    user = get_user_by_id(tg_id)

    start_weight = user["start_weight"]
    current_weight = data['current_weight']
    result_weight = round(float(current_weight) - float(start_weight),1)

    update_weight(tg_id, current_weight)

    if not isinstance(query.message, Message):
        return
    await (query.message.edit_text(
        "✅ Вагу успішно оновлено!\n\n"
        f"Початкова вага: {start_weight} кг\n"
        f"Актуальна вага: {current_weight} кг\n"
        f"Загальний результат: {result_weight} кг\n"
        f"Продовжуйте рухатися до своєї мети поступово та дотримуйтеся рекомендацій лікаря 🌿", reply_markup=main_menu
    ))

    await state.clear()
    await query.answer()
