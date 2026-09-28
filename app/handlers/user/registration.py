from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.inline_link_keyboard import get_inline_link_keyboard
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.utils.validators import * # тимчасовий імпорт всіх функцій, обовїязково оптимізувати
from app.states.user.registration import RegistrationStates
from app.database.repositories.user_repository import user_repository

router = Router()


def get_phone_share_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📱 Поділитися номером телефону",
                request_contact=True
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_confirm_registration_keyboard():
    keyboard = InlineKeyboardMarkup(
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
    return keyboard


async def show_registration_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()

    text = (f"✅ Перевірте введені дані\n\n"
            f"👤 ПІБ: {data["full_name"]}\n"
            f"📏 Зріст: {data["height"]}\n"
            f"⚖️ Актуальна вага: {data["current_weight"]} кг\n"
            f"🎯 Бажана вага: {data["target_weight"]} кг\n"
            f"📱 Телефон: {data["phone"]}\n\n"
            f"Якщо все вказано правильно — підтвердьте реєстрацію."
            )

    await message.answer(
        text,
        reply_markup=get_confirm_registration_keyboard()
    )


@router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    await state.set_state(RegistrationStates.wait_for_name)
    await callback.message.edit_text(
        "👤 <b>Як вас звати?</b>\n\n"
        "Напишіть одним повідомленням ваше прізвище, ім’я та по батькові.\n\n"
        "Наприклад:\n"
        "<i>Левицька Евеліна Андріївна</i>"
    )
    return


@router.message(RegistrationStates.wait_for_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text is None:
        return
    full_name = message.text

    if not is_valid_full_name(full_name):
        await message.answer(
            "⚠️ Введіть коректне ім’я та прізвище.\n\n"
            "Наприклад: <i>Левицька Евеліна Андріївна</i>"
        )
        return

    await state.update_data(full_name=full_name)

    await state.set_state(RegistrationStates.wait_for_height)
    await message.answer(
        "📏 <b>Який у вас зріст?</b>\n\n"
        "Напишіть зріст у сантиметрах одним числом.\n\n"
        "Наприклад: <i>168</i>"
    )


@router.message(RegistrationStates.wait_for_height)
async def process_height(message: Message, state: FSMContext):
    if message.text is None:
        return
    height = message.text

    if not is_valid_height(height):
        await message.answer(
            "⚠️ Вкажіть коректний зріст у сантиметрах.\n"
            "Наприклад: <i>168</i>"
        )
        return

    await state.update_data(height=height)

    await state.set_state(RegistrationStates.wait_for_current_weight)
    await message.answer(
        "⚖️ <b>Яка ваша поточна вага?</b>\n\n"
        "Вкажіть вагу у кілограмах.\n\n"
        "Наприклад: <i>92 або 92,5</i>"
    )


@router.message(RegistrationStates.wait_for_current_weight)
async def process_current_weight(message: Message, state: FSMContext):
    if message.text is None:
        return
    current_weight = message.text

    if not is_valid_weight(current_weight):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n"
            "Наприклад: <i>84.3</i>"
        )
        return

    current_weight = float(current_weight.replace(",", "."))
    await state.update_data(current_weight=current_weight)

    await state.set_state(RegistrationStates.wait_for_target_weight)
    await message.answer(
        "🎯 <b>Якої ваги ви хотіли б досягти?</b>\n\n"
        "Вкажіть бажану вагу у кілограмах.\n\n"
        "Наприклад: <i>80</i>"
    )


@router.message(RegistrationStates.wait_for_target_weight)
async def process_target_weight(message: Message, state: FSMContext):
    if message.text is None:
        return
    target_weight = message.text

    if not is_valid_weight(target_weight):
        await message.answer(
            "⚠️ Вкажіть коректну вагу в кілограмах.\n"
            "Наприклад: <i>80</i>"
        )
        return

    target_weight = float(target_weight.replace(",", "."))
    await state.update_data(target_weight=target_weight)

    share_phone_text = (
        "📱 <b>Поділіться вашим номером телефону</b>\n\n"
        "Він потрібен, щоб лікар міг звʼязатися з вами щодо консультації\n\n"
        "🔖Для цього натисніть кнопку <b>«📱 Поділитися номером телефону»</b>, яка розташована внизу екрана, під полем для введення повідомлення.")

    await state.set_state(RegistrationStates.wait_for_phone)
    await message.answer(share_phone_text, reply_markup=get_phone_share_keyboard())


@router.message(RegistrationStates.wait_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.contact is None:
        return

    phone = message.contact.phone_number
    if not is_valid_phone(phone):
        await message.answer(
            "⚠️ Будь ласка, вкажіть коректний номер телефону."
            "\n\nНаприклад: 380671234567")
        return

    await state.update_data(phone=phone)

    await message.answer(
        "✅ Номер телефону отримано",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(RegistrationStates.confirm_registration)
    await show_registration_confirmation(message=message, state=state)


@router.callback_query(RegistrationStates.confirm_registration, F.data == "confirm_registration")
async def process_registration_confirmation(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return

    await query.answer()
    data = await state.get_data()

    tg_id = query.from_user.id
    full_name = data["full_name"]
    phone = data["phone"]
    height=data["height"]
    start_weight = data["current_weight"]
    current_weight = data["current_weight"]
    target_weight = data["target_weight"]
    next_weight_request_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    user_id = user_repository.create(
        tg_id,
        full_name,
        phone,
        height,
        start_weight,
        current_weight,
        target_weight,
        next_weight_request_at
    )

    if not user_id:
        await query.message.answer(

            "⚠️ Не вдалося завершити реєстрацію. Спробуйте ще раз."
        )
        return

    await state.clear()

    text = (
        "🌿 <b>Заповнення медичної анкети</b>\n\n"
        "Перед початком співпраці з Elvia пропонуємо вам заповнити невелику анкету. "
        "Вона допоможе спеціалісту краще познайомитися з вами, дізнатися про стан вашого здоров’я, "
        "спосіб життя, попередній досвід і очікування від терапії.\n\n"
        "Будь ласка, відповідайте уважно та відверто — це допоможе зробити майбутню консультацію "
        "безпечною та максимально корисною саме для вас.\n\n"
        "Заповнення анкети триватиме приблизно 10–15 хвилин. Уся надана інформація залишається конфіденційною "
        "та використовується лише для проведення консультації й персонального супроводу.\n\n"
        "Після отримання анкети спеціаліст ознайомиться з вашими відповідями та зв’яжеться з вами, "
        "щоб разом узгодити наступний крок ☺️"
    )

    await query.message.edit_text("✅ Реєстрацію успішно завершено")
    await query.message.answer(text, reply_markup=get_inline_link_keyboard())
    await query.message.answer(
        "🌿 <b>Зовсім скоро вам стане доступне головне меню</b>\n"
        "Після консультації з лікарем і призначення індивідуальної терапії "
        "ви зможете користуватися всіма можливостями бота 💚"
        , reply_markup=get_main_menu_keyboard())

@router.callback_query(RegistrationStates.confirm_registration, F.data == "edit_registration")
async def edit_registration(callback: CallbackQuery, state: FSMContext):
    if not isinstance(callback.message, Message):
        return

    await callback.answer()
    await state.clear()

    await start_registration(callback=callback, state=state)


@router.message(F.text == "🏠 Головне меню")
async def back_to_menu(message: Message):
    await message.answer('Головне меню:', reply_markup=get_main_menu_keyboard())