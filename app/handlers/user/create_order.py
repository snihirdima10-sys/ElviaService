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
        [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")],
    ])

def get_cancel_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
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
                    text="🔄 Змінити дані",
                    callback_data="edit_delivery_data")
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Скасувати",
                    callback_data="cancel:order")
            ]
    ])

def get_payment_details_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оплачено", callback_data="confirm_payment")],
            [InlineKeyboardButton(text="↩️ Скасувати", callback_data="cancel:order")]
    ])

def get_success_create_order() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Мої замовлення")],
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True
    )

def get_delivery_methods_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Відділення", callback_data="method:branch")],
            [InlineKeyboardButton(text="Поштомат", callback_data="method:parcel_locker")],
            [InlineKeyboardButton(text="Адресна доставка", callback_data="method:courier_delivery")],
        ]
    )
# ==============================================================================================================

async def show_order_details(message: Message, state: FSMContext) -> None:
    if message.from_user is None:
        return

    user = user_repository.get_by_tg_id(message.from_user.id)
    await state.update_data(phone=user["phone"],)
    order_data = await state.get_data()

    text = (
        "📦 <b>Перевірте ваше замовлення</b>\n\n"
        f"💉 Препарат: <b>{order_data["medication_name"]}</b>\n"
        f"Дозування: <b>{order_data["dose_value_mg"]} мг</b>\n"
        f"Період: <b>{format_weeks(order_data["weeks_count"])}</b>\n"
        f"До сплати: <b>{order_data["total_price"]:.0f} грн</b>\n\n"
        f"👤 Одержувач: <b>{user["full_name"]}</b>\n"
        f"Телефон: <b>{user["phone"]}</b>\n\n"
        f"🚚 <b>Доставка</b>\n{order_data["delivery_data"]}\n\n"
        f"Будь ласка, перевірте вказані дані перед підтвердженням замовлення."
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
        "🛒 <b>Оформлення замовлення</b>\n\n"
        "Ваше поточне призначення:\n\n"
        f"Препарат — <b>{medication_name}</b>\n"
        f"Дозування — <b>{dose_value_mg} мг</b> один раз на тиждень\n\n"
        "<i>Оберіть бажану тривалість терапії, щоб перейти до оформлення замовлення</i> 🤍")


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
        "📦 Умови оформлення:\n\n"
        "Ваше замовлення:\n\n"
        f"Препарат — <b>{order_data["medication_name"]} {order_data["dose_value_mg"]} мг</b>\n"
        f"Тривалість — <b>{format_weeks(weeks_count)}</b>\n"
        f"До сплати — <b>{total_price} грн</b>\n\n"
        "Доставка здійснюється Новою поштою по Україні. Вартість доставки оплачує отримувач відповідно до тарифів перевізника.\n\n"
        "Після підтвердження оплати очікуйте повідомлення щодо оформлення та відправлення замовлення протягом 24 годин у застосунку Нова пошта 🙌🏻\n\n"
        "<i>Зверніть увагу: через воєнну ситуацію в країні строки доставки можуть бути збільшені на 1–3 дні. Дякуємо за ваше розуміння 🪴</i>"
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


@router.callback_query(F.data == "accept_order_terms")
async def request_city(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await state.update_data(message_id = query.message.message_id)
    await state.set_state(CreateOrderState.wait_for_city)
    await query.message.edit_text("Напишіть місто доставки", reply_markup=get_cancel_order_keyboard())


@router.message(CreateOrderState.wait_for_city)
async def process_city(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text is None:
        return
    data = await state.get_data()
    message_id = data.get("message_id")

    if message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message_id,
            reply_markup=None,
        )

    await state.update_data(city=message.text)
    await request_delivery_methods(message=message, state=state)


async def request_delivery_methods(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateOrderState.wait_for_delivery_method)
    await message.answer("Оберіть зручний спосіб доставки", reply_markup=get_delivery_methods_keyboard())


@router.callback_query(F.data.startswith("method:"), CreateOrderState.wait_for_delivery_method)
async def process_delivery_method(query: CallbackQuery, state: FSMContext) -> None:
    if query.data is None:
        return
    if not isinstance(query.message, Message):
        return
    method = query.data.split(":")[1]

    methods = ["branch", "parcel_locker", "courier_delivery"]

    if method not in methods:
        await query.message.edit_text("Щось пішло не так")
        return

    await state.update_data(method=method)

    await request_address(query=query, state=state)


async def request_address(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return
    await state.set_state(CreateOrderState.wait_for_address)
    data = await state.get_data()
    method = data.get("method")

    match method:
        case "branch":
            await query.message.edit_text("Введіть номер відділення")

        case "parcel_locker":
            await query.message.edit_text("Введіть номер поштомату")

        case "courier_delivery":
            await query.message.edit_text("Введіть адрес доставки")

        case _:
            return


@router.message(CreateOrderState.wait_for_address)
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

    address = message.text
    format_method = {"branch": "Відділення", "parcel_locker": "Поштомат", "courier_delivery":"Адреса"}
    delivery_data = (f"Місто: {order["city"]}\n"
                     f"{format_method[order["method"]]}: {address}")
    await state.update_data(delivery_data=delivery_data)
    await show_order_details(message=message, state=state)


@router.callback_query(F.data == "confirm_order", CreateOrderState.wait_for_order_confirmation)
async def show_payment_details(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    order_data = await state.get_data()

    text = (
        "💳 <b>Оплата замовлення</b>\n\n"
        "Ваше замовлення:\n\n"
        f"💉{order_data["medication_name"]} — {order_data["dose_value_mg"]} мг\n"
        f"📅Період: {format_weeks(order_data["weeks_count"])}\n"
        f"💳<b>До сплати: {order_data["total_price"]:.0f} грн</b>\n\n"
        "<b>Реквізити для оплати</b>\n\n"
        "Отримувач: [ПІБ / назва]\n"
        "IBAN: [номер рахунку]\n"
        "Призначення платежу: <b>Замовлення №1042</b>\n\n"
        "Після здійснення оплати натисніть <b>«Оплачено»</b> та надішліть підтвердження платежу.\n\n"
        "Дякуємо за ваше замовлення 🙌🏻🌿"
    )

    await state.set_state(CreateOrderState.wait_for_payment)
    await query.message.edit_text(text, reply_markup=get_payment_details_keyboard())


@router.callback_query(F.data == "confirm_payment", CreateOrderState.wait_for_payment)
async def create_order(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    await query.message.edit_reply_markup(reply_markup=None)

    order_data = await state.get_data()

    order_payload = {
        "tg_id": order_data["tg_id"],
        "user_phone": order_data["phone"],
        "dose_id": order_data["dose_id"],
        "weeks_count": order_data["weeks_count"],
        "discount": order_data["discount"],
        "total_price": order_data["total_price"],
        "delivery_data": f"{order_data['delivery_data']}",
        "status": "new"
    }

    order_id = order_repository.create(**order_payload)
    if not order_id:
        return
    await state.clear()

    text = (
        "📦 <b>Замовлення прийнято</b>\n\n"
        "Ваше замовлення успішно передано адміністратору та найближчим часом буде оброблено.\n\n"
        "Дякуємо, що обираєте Elvia 🤍"
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
    await request_city(query=query, state=state)


@router.callback_query(F.data == "change_period",CreateOrderState.wait_for_terms_confirmation)
async def change_period(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    tg_id = query.from_user.id
    active_therapy = therapy_repository.get_active_by_tg_id(tg_id)

    dose_id = active_therapy["dose_id"]
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
