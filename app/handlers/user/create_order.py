from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.states.user.create_order import CreateOrderState
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from container import Services
from keyboards.user import get_show_order_details_keyboard, build_select_period_keyboard, get_order_terms_keyboard, \
    get_cancel_order_keyboard, get_delivery_methods_keyboard, get_payment_details_keyboard, get_success_create_order
from services.order_service import OrderCreateData
from texts.user import format_order_details
from utils.formatter import format_weeks


async def show_order_details(message: Message, state: FSMContext, services: Services) -> None:
    if message.from_user is None:
        return

    user = services.user.get_user_by_tg_id(message.from_user.id)
    if user is None:
        return

    active_therapy = services.therapy.get_active_therapy_by_user_id(user.id)
    if active_therapy is None:
        return


    data = await state.get_data()
    await state.set_state(CreateOrderState.wait_for_order_confirmation)

    order_preview = services.order.build_order_preview(
        dose_id=data["dose_id"],
        weeks_count=data["weeks_count"],
        city=data["city"],
        delivery_method=data["delivery_method"],
        address=data["address"],
    )

    await message.answer(format_order_details(
        user=user,
        active_therapy=active_therapy,
        order_preview = order_preview
        ), reply_markup=get_show_order_details_keyboard())


router = Router()


@router.message(StateFilter(None), F.text == "🛒 Зробити замовлення")
async def show_periods(message: Message, state: FSMContext, services: Services) -> None:
    if message.from_user is None:
        return
    tg_id = message.from_user.id

    user_id = services.user.get_user_id_by_tg_id(tg_id)
    if user_id is None:
        return

    active_dose = services.therapy.get_active_therapy_by_user_id(user_id)

    if active_dose is None:
        await message.answer(
            "⚠️ Активне призначення не знайдено.\n\n"
            "Для оформлення замовлення необхідне актуальне "
            "дозування від лікаря.Будь ласка, зверніться до лікаря."
        )
        return

    text = (
        "🛒 <b>Оформлення замовлення</b>\n\n"
        "Ваше поточне призначення:\n\n"
        f"Препарат — <b>{active_dose.dose.medication}</b>\n"
        f"Дозування — <b>{active_dose.dose.dose_value} мг</b> один раз на тиждень\n\n"
        "<i>Оберіть бажану тривалість терапії, щоб перейти до оформлення замовлення</i> 🤍"
    )

    await state.update_data(
        user_id=user_id,
        dose_id=active_dose.dose.id
    )
    await state.set_state(CreateOrderState.wait_for_choose_period)
    await message.answer(text, reply_markup=build_select_period_keyboard(active_dose.dose.price))


@router.callback_query(F.data.startswith("period:"), CreateOrderState.wait_for_choose_period)
async def show_order_terms(query: CallbackQuery, state: FSMContext, services: Services) -> None:
    await query.answer()
    if query.data is None:
        return
    weeks_count = int(query.data.split(":")[1])

    data = await state.get_data()

    active_dose = services.dose.get_dose_by_dose_id(data["dose_id"])
    if active_dose is None:
        return

    total_price = services.order.calculate_total_price(
        price=active_dose.price,
        weeks_count=weeks_count,
        discount=services.order.calculate_discount(weeks_count)
    )

    text = (
        "📦 Умови оформлення:\n\n"
        "Ваше замовлення:\n\n"
        f"Препарат — <b>{active_dose.medication} {active_dose.dose_value} мг</b>\n"
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

    await state.update_data(delivery_method=method)
    await request_address(query=query, state=state)


async def request_address(query: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(query.message, Message):
        return
    await state.set_state(CreateOrderState.wait_for_address)
    data = await state.get_data()
    method = data.get("delivery_method")

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
async def process_delivery_data(message: Message, state: FSMContext, bot: Bot, services:Services):
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
    # format_method = {"branch": "Відділення", "parcel_locker": "Поштомат", "courier_delivery":"Адреса"}

    await state.update_data(address=address)
    await show_order_details(message=message, state=state, services=services)


@router.callback_query(F.data == "confirm_order", CreateOrderState.wait_for_order_confirmation)
async def show_payment_details(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    order_data = await state.get_data()

    active_dose = services.dose.get_dose_by_dose_id(order_data["dose_id"])
    if active_dose is None:
        return


    price = active_dose.price
    weeks_count = order_data["weeks_count"]
    total_price = services.order.calculate_total_price(
        price=price,
        weeks_count=weeks_count,
        discount=services.order.calculate_discount(weeks_count),
    )

    await state.update_data(total_price=total_price)

    text = (
        "💳 <b>Оплата замовлення</b>\n\n"
        "Ваше замовлення:\n\n"
        f"💉{active_dose.medication} — {active_dose.dose_value} мг\n"
        f"📅Період: {format_weeks(order_data["weeks_count"])}\n"
        f"💳<b>До сплати: {total_price:.0f} грн</b>\n\n"
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
async def create_order(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    data = await state.get_data()

    order_data = OrderCreateData(
        user_id=data["user_id"],
        dose_id=data["dose_id"],
        weeks_count=data["weeks_count"],
        city=data["city"],
        delivery_method=data["delivery_method"],
        address=data["address"]
    )

    order_id = services.order.create_order(order_data)
    if order_id:
        await query.message.edit_text("✅ Замовлення успішно оформлено")
        await query.message.answer(
            "📦 <b>Замовлення прийнято</b>\n\n"
            "Ваше замовлення успішно передано адміністратору та найближчим часом буде оброблено.\n\n"
            "Дякуємо, що обираєте Elvia 🤍", reply_markup=get_success_create_order()
        )
    else:
        await query.message.edit_text("Щось пішло не так")


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
async def change_period(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    data = await state.get_data()
    active_therapy = services.therapy.get_active_therapy_by_user_id(data["user_id"])
    if active_therapy is None:
        return

    await state.set_state(CreateOrderState.wait_for_choose_period)
    await query.message.edit_text("Оберіть період терапії, на який хочете оформити замовлення:", reply_markup=build_select_period_keyboard(
        dose_price=active_therapy.dose.price,))
