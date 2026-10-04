import logging
import sqlite3
from uuid import uuid4
from html import escape

from config import PAYMENT_IBAN, PAYMENT_RECIPIENT, PAYMENT_PURPOSE, PAYMENT_TEST_MODE

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.states.user.create_order import CreateOrderState
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.container import Services
from app.keyboards.user import get_show_order_details_keyboard, build_select_period_keyboard, get_order_terms_keyboard, \
    get_cancel_order_keyboard, get_delivery_methods_keyboard, get_payment_details_keyboard, get_success_create_order
from app.services.order_service import OrderCreateData
from app.texts.user import format_order_details
from app.utils.formatter import format_weeks, format_money
from app.utils.validators import is_valid_city, is_valid_delivery_address


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
logger = logging.getLogger(__name__)


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
            "🌿 <b>Потрібно уточнити призначення</b>\n\n"
            "Наразі в системі немає актуального дозування для оформлення замовлення.\n\n"
            "Будь ласка, зв’яжіться з лікарем — він допоможе уточнити вашу терапію та, за потреби, оновить призначення.\n\n"
            "Після цього оформлення замовлення буде доступне 🤍",
            parse_mode="HTML", reply_markup=get_main_menu_keyboard(),
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
        "📦 <b>Умови оформлення</b>\n\n"
        "<b>Ваше замовлення:</b>\n\n"
        f"Препарат — <b>{escape(active_dose.medication)} {str(active_dose.dose_value).replace('.', ',')} мг</b>\n"
        f"Тривалість — <b>{format_weeks(weeks_count)}</b>\n"
        f"До сплати — <b>{format_money(total_price)} грн</b>\n\n"
        "💳 <b>Оплата замовлення</b>\n\n"
        "Для оформлення та підготовки замовлення передбачена <b>повна оплата перед відправленням</b>.\n\n"
        "🚚 <b>Доставка</b>\n\n"
        "Доставка здійснюється Новою поштою по Україні. Вартість доставки оплачує отримувач відповідно до тарифів перевізника.\n\n"
        "Після підтвердження оплати очікуйте повідомлення про оформлення та відправлення замовлення протягом <b>24 годин</b> у застосунку Нова пошта 🙌🏻\n\n"
        "🛡 <b>Турбота про ваше замовлення</b>\n\n"
        "Якщо через обставини воєнного часу посилка буде втрачена під час доставки, ми подбаємо про повторне відправлення вашого замовлення <b>без додаткової оплати з вашого боку</b>.\n\n"
        "Зверніть увагу: <i>через воєнну ситуацію строки доставки можуть бути збільшені на <b>1–3 дні</b>. Дякуємо за розуміння 🪴</i>"
    )
    if not isinstance(query.message, Message):
        return

    await state.update_data(
        weeks_count=weeks_count,
    )
    await state.set_state(CreateOrderState.wait_for_terms_confirmation)
    await query.message.edit_text(text, reply_markup=get_order_terms_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "accept_order_terms", CreateOrderState.wait_for_terms_confirmation)
async def request_city(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    if not isinstance(query.message, Message):
        return

    await state.update_data(message_id = query.message.message_id)
    await state.set_state(CreateOrderState.wait_for_city)
    await query.message.edit_text("Напишіть місто доставки", reply_markup=get_cancel_order_keyboard())


@router.message(CreateOrderState.wait_for_city)
async def process_city(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text is None or not is_valid_city(message.text):
        await message.answer("Введіть назву міста текстом, наприклад: Київ.")
        return
    data = await state.get_data()
    message_id = data.get("message_id")

    if message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message_id,
            reply_markup=None,
        )

    await state.update_data(city=message.text.strip())
    await request_delivery_methods(message=message, state=state)


async def request_delivery_methods(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateOrderState.wait_for_delivery_method)
    await message.answer("Оберіть зручний спосіб доставки", reply_markup=get_delivery_methods_keyboard())


@router.callback_query(F.data.startswith("method:"), CreateOrderState.wait_for_delivery_method)
async def process_delivery_method(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
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
            await query.message.edit_text("Введіть номер відділення", reply_markup=get_cancel_order_keyboard())

        case "parcel_locker":
            await query.message.edit_text("Введіть номер поштомату", reply_markup=get_cancel_order_keyboard())

        case "courier_delivery":
            await query.message.edit_text("Введіть адресу доставки", reply_markup=get_cancel_order_keyboard())

        case _:
            return


@router.message(CreateOrderState.wait_for_address)
async def process_delivery_data(message: Message, state: FSMContext, bot: Bot, services:Services):
    order = await state.get_data()
    if message.text is None or not is_valid_delivery_address(message.text, order.get("delivery_method")):
        await message.answer("Введіть додатний номер відділення/поштомату або повну адресу для кур’єрської доставки.")
        return
    delivery_message_id = order.get("delivery_message_id")

    if delivery_message_id is not None:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=delivery_message_id,
            reply_markup=None,
        )

    address = message.text.strip()
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

    await state.update_data(total_price=total_price, checkout_token=uuid4().hex)

    text = (
        "💳 <b>Оплата замовлення</b>\n\n"
        "<b>Ваше замовлення</b>\n\n"
        f"💉 Препарат: {escape(active_dose.medication)} — {str(active_dose.dose_value).replace('.', ',')} мг\n"
        f"📅 Період: {format_weeks(order_data['weeks_count'])}\n"
        f"💳 До сплати: <b>{format_money(total_price)} грн</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "🏦 <b>Реквізити для оплати</b>\n\n"
        f"<b>Отримувач:</b>\n{escape(PAYMENT_RECIPIENT or '[ПІБ / назва]')}\n\n"
        f"<b>IBAN:</b>\n{escape(PAYMENT_IBAN or '[номер рахунку]')}\n\n"
        f"<b>Призначення платежу:</b>\n{escape(PAYMENT_PURPOSE)}\n\n"
        "Скопіюйте необхідні реквізити за допомогою кнопок нижче.\n\n"
        "━━━━━━━━━━━━━━\n\n"
        "✨ <b>Після оплати</b>\n\n"
        "Натисніть <b>«Оплачено»</b> та надішліть квитанцію у форматі PDF або скріншот.\n\n"
        "<i>Після перевірки платежу ви отримаєте повідомлення в боті про підтвердження оплати.</i>\n\n"
        "Дякуємо, що обираєте <b>Elvia</b> 🌿"
    )

    await state.set_state(CreateOrderState.wait_for_payment)
    if PAYMENT_TEST_MODE:
        text = '🧪 <b>Тестовий режим — не здійснюйте оплату.</b>\nРеквізити вигадані та непридатні для переказу.\n\n' + text
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=get_payment_details_keyboard(
        iban=PAYMENT_IBAN, recipient=PAYMENT_RECIPIENT, purpose=PAYMENT_PURPOSE,
    ))


@router.callback_query(F.data == "confirm_payment", CreateOrderState.wait_for_payment)
async def request_payment_receipt(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    await state.set_state(CreateOrderState.wait_for_payment_receipt)
    await query.message.edit_text(
        '📎 <b>Підтвердження оплати</b>\n\nНадішліть квитанцію у форматі PDF або скріншот оплати (фото чи файл JPG/PNG/WEBP).\n\n'
        'Замовлення буде оформлено після завантаження підтвердження.',
        reply_markup=get_cancel_order_keyboard(),
    )


@router.message(CreateOrderState.wait_for_payment_receipt)
async def receive_payment_receipt(message: Message, state: FSMContext, services: Services):
    if not message.from_user:
        return
    file_name = None
    if message.photo:
        file_id, receipt_type = message.photo[-1].file_id, 'photo'
    elif message.document:
        document = message.document
        file_name = document.file_name
        allowed = {'application/pdf': ('.pdf',), 'image/jpeg': ('.jpg', '.jpeg'),
                   'image/png': ('.png',), 'image/webp': ('.webp',)}
        extensions = allowed.get(document.mime_type, ())
        if not extensions or (file_name and not file_name.lower().endswith(extensions)):
            await message.answer('Надішліть квитанцію PDF або скріншот у форматі JPG, PNG чи WEBP.')
            return
        file_id, receipt_type = document.file_id, 'document'
    else:
        await message.answer('Потрібен файл PDF або скріншот оплати. Текстове повідомлення не є підтвердженням.')
        return
    data = await state.get_data()
    user_id = services.user.get_user_id_by_tg_id(message.from_user.id)
    if user_id is None or user_id != data.get('user_id'):
        await message.answer('Не вдалося визначити ваше замовлення. Відкрийте головне меню через /start.')
        return
    if not data.get('checkout_token'):
        data['checkout_token'] = uuid4().hex
        await state.update_data(checkout_token=data['checkout_token'])

    order_data = OrderCreateData(
        user_id=data["user_id"],
        dose_id=data["dose_id"],
        weeks_count=data["weeks_count"],
        city=data["city"],
        delivery_method=data["delivery_method"],
        address=data["address"],
        receipt_file_id=file_id,
        receipt_type=receipt_type,
        receipt_file_name=file_name,
        checkout_token=data['checkout_token'],
    )

    try:
        order_id = services.order.create_order(order_data)
    except (sqlite3.Error, ValueError):
        logger.exception('Could not save order receipt for user %s', user_id)
        await message.answer('Не вдалося зберегти замовлення. Надішліть квитанцію ще раз.')
        return
    if order_id:
        await message.answer(
            f"📦 <b>Замовлення №{order_id} прийнято</b>\n\n"
            "Дякуємо! Ми отримали ваше замовлення та квитанцію про оплату.\n\n"
            "🔎 <b>Оплата очікує підтвердження</b>\n\n"
            "Наша команда перевірить платіж найближчим часом. Щойно оплату буде підтверджено, ви отримаєте <b>повідомлення в боті</b>.\n\n"
            "Після підтвердження ми розпочнемо підготовку вашого замовлення до відправлення.\n\n"
            "Дякуємо, що обираєте <b>Elvia</b> 🌿", reply_markup=get_success_create_order()
        )
        await state.clear()
    else:
        await message.answer("Не вдалося оформити замовлення. Надішліть квитанцію ще раз.")


@router.callback_query(F.data == "cancel:order", StateFilter(CreateOrderState))
async def cancel_order(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if not isinstance(query.message, Message):
        return

    await state.clear()

    await query.message.edit_reply_markup(reply_markup=None)
    await query.message.answer("❌ Замовлення скасоване", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "edit_delivery_data", CreateOrderState.wait_for_order_confirmation)
async def edit_delivery_data(query: CallbackQuery, state: FSMContext):
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
