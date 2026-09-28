from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.database.repositories.therapy_repository import therapy_repository
from app.database.repositories.order_repository import order_repository
from app.database.repositories.user_repository import user_repository
from app.handlers.user.progress import format_weeks
from app.states.user.create_order import CreateOrderState
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.utils.validators import validate_delivery_data


# ===================================================KEYBOARDS===================================================

def build_select_period_keyboard(dose_price):
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"1 тиждень — {dose_price:.2f} грн",
                    callback_data="period:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"2 тиждень — {2 * dose_price * 0.9} грн",
                    callback_data="period:2"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"4 тиждень — {4 * dose_price * 0.8} грн",
                    callback_data="period:4"
                )
            ]
        ])
    return inline_keyboard

def get_order_terms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Продовжити", callback_data="accept_order_terms")],
        [InlineKeyboardButton(text="🔄 Змінити період", callback_data="change_period")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel:order")],
    ])

def get_cancel_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel:order")]
        ]
    )

def get_show_order_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити замовлення",
                    callback_data="confirm_order")
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Змінити дані",
                    callback_data="edit_delivery_data")
            ]
    ])

def get_payment_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатив(ла)", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel:order")]
    ])

def get_success_create_order() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 МоЇ замовлення")],
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True
    )

# ==============================================================================================================

async def show_order_details(message: Message, state: FSMContext) -> None:
    order_data = await state.get_data()
    text = (
            "📦 Перевірте ваше замовлення\n\n"
            f"💉 Препарат: {order_data["medication_name"]}\n"
            f"⚖️ Дозування: {order_data["dose_value_mg"]} мг\n"
            f"📅 Період: {format_weeks(order_data["weeks_count"])}\n"
            f"💳 Сума: {order_data["total_price"]}\n"
            f"👤 Одержувач: {order_data["full_name"]}\n"
            f"📱 Телефон: {order_data["user_phone"]}\n"
            f"🏙 Місто: {order_data["city"]}\n"
            f"📮 Доставка: Нова пошта, {order_data["branch"]}\n\n"
            "Перевірте правильність даних перед підтвердженням."
        )

    await state.set_state(CreateOrderState.wait_for_order_confirmation)
    await message.answer(text, reply_markup=get_show_order_details_keyboard())

# ==============================================================================================================


router = Router()


@router.message(StateFilter(None), F.text == "🛒 Зробити замовлення")
async def show_periods(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    tg_id = message.from_user.id
    user_id = user_repository.get_by_tg_id(tg_id)["id"]
    active_dose = therapy_repository.get_active_by_tg_id(tg_id)

    if active_dose is None:
        await message.answer(
            "⚠️ Активне призначення не знайдено.\n\n"
            "Для оформлення замовлення необхідне актуальне "
            "дозування від лікаря.Будь ласка, зверніться до лікаря."
        )
        return

    dose_id = active_dose["dose_id"]
    medication_name = active_dose["medication"]
    dose_value_mg = active_dose["dose_value"]
    dose_price = active_dose["price"]

    text = (
        "🛒 Зробити замовлення\n\n"
        "Ваше актуальне призначення:\n\n"
        f"💉 Препарат: {medication_name}\n"
        f"⚖️ Дозування: {dose_value_mg} мг на тиждень\n\n"
        "Оберіть період терапії, на який хочете оформити замовлення:"
    )


    await state.update_data(
        tg_id = tg_id,
        user_id=user_id,
        dose_price=dose_price,
        medication_name=medication_name,
        dose_value_mg=dose_value_mg,
        dose_id=dose_id,
        )

    await state.set_state(CreateOrderState.wait_for_choose_period)
    await message.answer(text, reply_markup=build_select_period_keyboard(dose_price))


@router.callback_query(F.data.startswith("period:"), CreateOrderState.wait_for_choose_period)
async def show_order_terms(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if query.data is None:
        return

    weeks_count = int(query.data.split(":")[1])

    match weeks_count:
        case 1:
            discount_percent = 0
        case 2:
            discount_percent = 10
        case 4:
            discount_percent = 20
        case _:
            return

    order_data = await state.get_data()
    dose_price = order_data["dose_price"]
    total_price = round(weeks_count * dose_price * (1 - discount_percent / 100), 1)

    text = (
        "📦 Умови замовлення\n\n"
        "Ваш вибір:\n\n"
        f"💉 {order_data["medication_name"]} — {order_data["dose_value_mg"]} мг\n"
        f"📅 Період: {format_weeks(weeks_count)}\n"
        f"💳 До сплати: {total_price} грн\n\n"
        "Доставка здійснюється Новою поштою по Україні. Вартість доставки сплачує отримувач "
        "відповідно до тарифів перевізника.Оплата здійснюється у повному розмірі. Після оформлення заявки "
        "лікар особисто зв’яжеться з вами, підтвердить замовлення та надасть реквізити для оплати."
    )
    if not isinstance(query.message, Message):
        return

    await state.update_data(
        weeks_count=weeks_count,
        discount=discount_percent,
        total_price=total_price
    )

    await state.set_state(CreateOrderState.wait_for_terms_confirmation)
    await query.message.edit_text(text, reply_markup=get_order_terms_keyboard())


@router.callback_query(F.data == "accept_order_terms", CreateOrderState.wait_for_terms_confirmation)
async def request_delivery_data(query: CallbackQuery, state: FSMContext):
    await query.answer()
    text = (
        "📋 Дані для доставки\n"
        "Надішліть одним повідомленням:\n"
        "ПІБ:\n "
        "Номер телефону:\n"
        "Місто:\n"
        "Номер відділення або поштомату Нової пошти:\n"
        "Приклад:\n"
        "Іваненко Анна Сергіївна\n"
        "+380 67 123 45 67\n"
        "Київ\n"
        "Відділення №25")

    if not isinstance(query.message, Message):
        return

    await state.update_data(
        delivery_message_id=query.message.message_id,
    )

    await query.answer()
    await state.set_state(CreateOrderState.wait_for_delivery_data)
    await query.message.edit_text(text, reply_markup=get_cancel_order_keyboard())


@router.message(CreateOrderState.wait_for_delivery_data)
async def process_delivery_data(message: Message, state: FSMContext, bot: Bot):
    if message.text is None:
        return
    order = await state.get_data()
    delivery_message_id = order.get("delivery_message_id")

    if delivery_message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=delivery_message_id,
            reply_markup=None,
        )

    delivery_data = validate_delivery_data(message.text)

    await state.update_data(
        full_name=delivery_data["full_name"],
        user_phone=delivery_data["phone"],
        city=delivery_data["city"],
        branch=delivery_data["branch"],
    )

    await show_order_details(message=message, state=state)



@router.callback_query(F.data == "confirm_order", CreateOrderState.wait_for_order_confirmation)
async def show_payment_details(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    order_data = await state.get_data()

    text = (
        "💳 ОПЛАТА ЗАМОВЛЕННЯ\n\n"
        f"{order_data["medication_name"]} · {order_data["dose_value_mg"]} мг · {format_weeks(order_data["weeks_count"])}\n"
        f"Сума до оплати: {order_data["total_price"]} грн\n"
        "Будь ласка, оплатіть повну суму за реквізитами:\n"
        "Отримувач: [ПІБ / назва]\n"
        "IBAN: [номер рахунку]\n"
        "Призначення платежу: Замовлення №1042\n\n"
        "Після оплати натисніть «Я оплатив(ла)» та надішліть підтвердження платежу. "
    )

    await state.set_state(CreateOrderState.wait_for_payment)
    await query.message.edit_text(text, reply_markup=get_payment_details_keyboard())


@router.callback_query(F.data == "confirm_payment", CreateOrderState.wait_for_payment)
async def create_order(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    if not isinstance(query.message, Message):
        return
    await query.message.edit_reply_markup(reply_markup=None)

    order_data = await state.get_data()

    order_payload = {
        "tg_id": order_data["tg_id"],
        "user_phone": order_data["user_phone"],
        "dose_id": order_data["dose_id"],
        "weeks_count": order_data["weeks_count"],
        "discount": order_data["discount"],
        "total_price": order_data["total_price"],
        "delivery_data": f"{order_data["city"]} {order_data['branch']}",
        "status": "new"

    }

    order_id = order_repository.create(**order_payload)
    if not order_id:
        return
    await state.clear()

    text = (
        "Вашу заявку передано лікарю. "
        "Лікар перевірить надходження коштів і повідомить про подальше оформлення.\n"
        "⚠️ Не здійснюйте оплату за реквізитами, отриманими від сторонніх осіб."
    )

    await query.message.edit_text("✅ Замовлення успішно оформлено")
    await query.message.answer(text, reply_markup=get_success_create_order())


@router.callback_query(F.data == "cancel:order")
async def cancel_order(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    await state.clear()

    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer("❌ Замовлення скасоване", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "edit_delivery_data")
async def edit_delivery_data(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await request_delivery_data(query=query, state=state)



@router.callback_query(F.data == "change_period",CreateOrderState.wait_for_terms_confirmation)
async def change_period(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    tg_id = query.from_user.id
    active_therapy = therapy_repository.get_active_by_tg_id(tg_id)

    dose_id = active_therapy["id"]
    medication_name = active_therapy["medication"]
    dose_value_mg = active_therapy["dose_value"]
    dose_price = active_therapy["price"]

    await state.update_data(
        tg_id=tg_id,
        dose_price=dose_price,
        medication_name=medication_name,
        dose_value_mg=dose_value_mg,
        dose_id=dose_id
    )

    await state.set_state(CreateOrderState.wait_for_choose_period)
    await query.message.edit_text("Оберіть період терапії, на який хочете оформити замовлення:", reply_markup=build_select_period_keyboard(
        dose_price=active_therapy["price"],))
