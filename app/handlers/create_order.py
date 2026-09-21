from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.database.service import get_active_dose_by_user_id, add_order
from app.handlers.progress import format_weeks
from app.keyboards.main_menu import main_menu as main_keyboard


class OrderState(StatesGroup):
    choosing_period = State()
    waiting_for_terms_confirmation = State()
    waiting_for_delivery_data = State()
    waiting_for_order_confirmation = State()
    waiting_for_payment = State()


router = Router()


@router.message(F.text == "🛒 Зробити замовлення")
async def select_period(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    tg_id = message.from_user.id
    active_dose = get_active_dose_by_user_id(tg_id)

    if active_dose is None:
        await message.answer(
            "⚠️ Активне призначення не знайдено.\n\n"
            "Для оформлення замовлення необхідне актуальне "
            "дозування від лікаря.Будь ласка, зверніться до лікаря."
        )
        return

    dose_id = active_dose["id"]
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

    await state.update_data(
        tg_id = tg_id,
        dose_price=dose_price,
        medication_name=medication_name,
        dose_value_mg=dose_value_mg,
        dose_id=dose_id
        )

    await state.set_state(OrderState.choosing_period)
    await message.answer(text, reply_markup=inline_keyboard)


@router.callback_query(F.data.startswith("period:"), OrderState.choosing_period)
async def show_order_terms(query: CallbackQuery, state: FSMContext) -> None:
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Продовжити", callback_data="continue")],
        [InlineKeyboardButton(text="🔄 Змінити період", callback_data="change_period")],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])

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

    await query.answer()
    await state.set_state(OrderState.waiting_for_terms_confirmation)
    await query.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "continue", OrderState.waiting_for_terms_confirmation)
async def ask_delivery_data(query: CallbackQuery, state: FSMContext):
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel")],
        ]
    )

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
    await state.set_state(OrderState.waiting_for_delivery_data)
    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(
    StateFilter(
        OrderState.waiting_for_terms_confirmation,
        OrderState.waiting_for_order_confirmation,
    ),
    F.data == "change_period",
)
async def change_period(query: CallbackQuery, state: FSMContext):

    order_data = await state.get_data()
    dose_price = order_data["dose_price"]

    if dose_price is None:
        await state.clear()
        if not isinstance(query.message, Message):
            return

        await query.message.answer(
            "Дані замовлення недоступні. Почніть оформлення заново.",
            reply_markup=main_keyboard,
        )
        return

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

    if not isinstance(query.message, Message):
        return

    await query.answer()
    await state.set_state(OrderState.choosing_period)
    await query.message.edit_text(
        "Оберіть новий період замовлення:",
        reply_markup=inline_keyboard,
    )


@router.message(OrderState.waiting_for_delivery_data)
async def get_delivery_data(message: Message, state: FSMContext, bot: Bot):
    order_data = await state.get_data()
    delivery_message_id = order_data.get("delivery_message_id")

    if delivery_message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=delivery_message_id,
            reply_markup=None,
        )

    if message.text is None:
        return

    delivery_data = message.text.split("\n")

    full_name = delivery_data[0]
    user_phone = delivery_data[1]
    city = delivery_data[2]
    location = delivery_data[3]

    await state.update_data(
        full_name=full_name,
        user_phone=user_phone,
        city=city,
        location=location,
    )

    order_data = await state.get_data()

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити замовлення",
                    callback_data="confirm_order")
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Змінити дані",
                    callback_data="edit_data")
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Змінити період",
                    callback_data="change_period")
            ]
    ])

    text = (
        "📦 Перевірте ваше замовлення\n\n"
        f"💉 Препарат: {order_data["medication_name"]}\n"
        f"⚖️ Дозування: {order_data["dose_value_mg"]} мг\n"
        f"📅 Період: {format_weeks(order_data["weeks_count"])}\n"
        f"💳 Сума: {order_data["total_price"]}\n"
        f"👤 Одержувач: {order_data["full_name"]}\n"
        f"📱 Телефон: {order_data["user_phone"]}\n"
        f"🏙 Місто: {order_data["city"]}\n"
        f"📮 Доставка: Нова пошта, {order_data["location"]}\n\n"
        "Перевірте правильність даних перед підтвердженням."
    )

    await state.set_state(OrderState.waiting_for_order_confirmation)
    await message.answer(text, reply_markup=inline_keyboard)


@router.callback_query(F.data == "confirm_order", OrderState.waiting_for_order_confirmation)
async def show_payment_details(query: CallbackQuery, state: FSMContext):

    order_data = await state.get_data()

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатив(ла)", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]
    ])

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

    if not isinstance(query.message, Message):
        return

    await query.answer()
    await state.set_state(OrderState.waiting_for_payment)
    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data == "confirm_payment", OrderState.waiting_for_payment)
async def create_order(query: CallbackQuery, state: FSMContext):
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
        "delivery_data": f"{order_data["city"]} {order_data['location']}",
    }

    success = add_order(**order_payload)
    if not success:
        return


    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 МоЇ замовлення")],
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True
    )

    text = (
        "✅ Замовлення успішно оформлено\n\n"
        "Вашу заявку передано лікарю. "
        "Лікар перевірить надходження коштів і повідомить про подальше оформлення.\n"
        "⚠️ Не здійснюйте оплату за реквізитами, отриманими від сторонніх осіб."
    )

    if not isinstance(query.message, Message):
        return

    await state.clear()
    await query.answer(keyboard=None)
    await query.message.answer(text, reply_markup=reply_keyboard)


@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(query: CallbackQuery, state: FSMContext):
    if not isinstance(query.message, Message):
        return
    await query.message.edit_reply_markup(reply_markup=None)

    await state.clear()
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await query.message.answer("Головне меню:", reply_markup=main_keyboard)


@router.callback_query(F.data == "cancel")
async def cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await query.message.answer("❌ Замовлення скасоване", reply_markup=main_keyboard)