from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from app.keyboards.main_menu import main_menu
from aiogram import F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database.service import get_user_by_id, create_user
from app.utils.validators import validate_full_name, validate_height, validate_weight, validate_phone
from datetime import datetime, timedelta

class UserStates(StatesGroup):
    wait_for_name = State()
    wait_for_height = State()
    wait_for_current_weight = State()
    wait_for_target_weight = State()
    wait_for_phone = State()
    check_data = State()

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    if message.from_user is None:
        return
    items = get_user_by_id(int(message.from_user.id))

    if items is None:
        await state.set_state(UserStates.wait_for_name)

        await message.answer("🌿 Вітаємо в ElviaТут\n\nМи просто розповідаємо "
                             "про контроль ваги, харчування та проходження терапії.")

        await message.answer("👤 Як вас звати?\n\nНапишіть одним повідомленням ваше "
                             "прізвище, ім’я та по батькові.\n\nНаприклад:\nКоваль Анна Олександрівна")
    else:
        await message.answer("🌿 Вітаємо в ElviaТут\n\nМи просто розповідаємо "
                             "про контроль ваги, харчування та проходження терапії."
                             , reply_markup=main_menu)

@router.message(UserStates.wait_for_name)
async def wait_for_name(message: Message, state: FSMContext):
    if message.text is None:
        return
    full_name = message.text

    if not validate_full_name(full_name):
        await message.answer("⚠️ Введіть коректне ім’я та прізвище.\n\n"
            "Наприклад: Коваль Анна Олександрівна")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(UserStates.wait_for_height)

    await message.answer("📏 Який у вас зріст?\n\nНапишіть зріст у сантиметрах "
                         "одним числом.\n\nаприклад: 168")


@router.message(UserStates.wait_for_height)
async def wait_for_height(message: Message, state: FSMContext):
    if message.text is None:
        return

    height = message.text
    if not validate_height(height):
        await message.answer(
            "⚠️ Вкажіть коректний зріст у сантиметрах.\n"
            "Наприклад: 168"
        )
        return

    await state.update_data(height=height)
    await state.set_state(UserStates.wait_for_current_weight)

    await message.answer("⚖️ Яка ваша поточна вага?\n\nНапишіть вагу в кілограмах. "
                         "Можна вказати число з десятковою частиною.\n\nНаприклад: 92 або 92,5"
    )


@router.message(UserStates.wait_for_current_weight)
async def wait_for_current_weight(message: Message, state: FSMContext):
    if message.text is None:
        return

    current_weight = message.text
    if not validate_weight(current_weight):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n"
            "Наприклад: 84.3"
        )
        return

    current_weight = float(current_weight.replace(",", "."))
    await state.update_data(current_weight=current_weight)
    await state.set_state(UserStates.wait_for_target_weight)

    await message.answer("🎯 Якої ваги ви хотіли б досягти?\n\n"
                         "Напишіть бажану вагу в кілограмах.\n\nНаприклад: 80")


@router.message(UserStates.wait_for_target_weight)
async def wait_for_target_weight(message: Message, state: FSMContext):
    if message.text is None:
        return

    target_weight = message.text
    if not validate_weight(target_weight):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n"
            "Наприклад: 84.3"
        )
        return

    target_weight = float(target_weight.replace(",", "."))
    await state.update_data(target_weight=target_weight)
    await state.set_state(UserStates.wait_for_phone)

    phone_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(
            text="📱 Поділитися номером телефону",
            request_contact=True
            )
        ]
    ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("📱 Вкажіть ваш номер телефону.\n\n"
                         "Він потрібен, щоб лікар міг зв’язатися з вами "
                         "щодо консультації або замовлення.\nНатисніть "
                         "«Поділитися номером» або напишіть його одним повідомленням "
                         "у міжнародному форматі.\n\nНаприклад: +380XXXXXXXXX",
                         reply_markup=phone_keyboard
                         )


@router.message(UserStates.wait_for_phone)
async def wait_for_phone(message: Message, state: FSMContext):
    if message.contact is None:
        return

    phone = message.contact.phone_number
    if not validate_phone(phone):
        await message.answer("⚠️ Будь ласка, вкажіть коректний номер телефону."
                             "\n\nНаприклад: 380671234567")
        return

    await state.update_data(phone=phone)
    await state.set_state(UserStates.check_data)

    await message.answer(
        "✅ Номер телефону отримано.",
        reply_markup=ReplyKeyboardRemove()
    )

    data = await state.get_data()

    text = (f"✅ Перевірте введені дані\n\n"
            f"👤 ПІБ: {data["full_name"]}\n"
            f"📏 Зріст: {data["height"]}\n"
            f"⚖️ Актуальна вага: {data["current_weight"]} кг\n"
            f"🎯 Бажана вага: {data["target_weight"]} кг\n"
            f"📱 Телефон: {data["phone"]}\n\n"
            f"Якщо все вказано правильно — підтвердьте реєстрацію.")

    menu_check = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити",
                    callback_data="confirm_registration"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Змінити дані",
                    callback_data="edit_registration"
                )
            ]
        ]
    )


    await message.answer(
        text,
        reply_markup=menu_check
    )


@router.callback_query(
    UserStates.check_data,
    F.data == "confirm_registration")
async def confirm_registration(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    tg_id = query.from_user.id
    full_name = data["full_name"]
    phone = data["phone"]
    height=data["height"]
    start_weight = data["current_weight"]
    current_weight = data["current_weight"]
    target_weight = data["target_weight"]
    next_weight_request_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    success = create_user(
        tg_id,
        full_name,
        phone,
        height,
        start_weight,
        current_weight,
        target_weight,
        next_weight_request_at
    )
    if not success:
        await query.message.answer(
            "⚠️ Не вдалося завершити реєстрацію. Спробуйте ще раз."
        )
        await query.answer()
        return

    await state.clear()
    await query.answer()

    await query.message.answer(
        "✅ Реєстрацію успішно завершено.",
        reply_markup=main_menu
    )


@router.callback_query(
    UserStates.check_data,
    F.data == "edit_registration"
)
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await state.set_state(UserStates.wait_for_name)

    await callback.message.edit_text("👤 Як вас звати?\n\nНапишіть одним повідомленням ваше "
                             "прізвище, ім’я та по батькові.\n\nНаприклад:\nКоваль Анна Олександрівна")

    await callback.answer()


@router.message(F.text == "🏠 Головне меню")
async def back_to_menu(message: Message):
    await message.answer('Головне меню:', reply_markup=main_menu)