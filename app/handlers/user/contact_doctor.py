from html import escape
import logging

from aiogram import Router
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types  import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from app.container import Services
from app.database.repositories.consultation_repository import get_or_create_request, get_request, change_status
from app.texts.consultation import CONSULTATION_OFFER_TEXT, CONSULTATION_PENDING_TEXT, CONSULTATION_CONFIRMED_TEXT
from config import DOCTOR_URL, DOCTOR_ID, PAYMENT_IBAN, PAYMENT_RECIPIENT, PAYMENT_PURPOSE, PAYMENT_TEST_MODE

router = Router()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Головне меню")]
    ],
    resize_keyboard=True
)

def inline_keyboard(*buttons):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in buttons
    ])


def offer_keyboard():
    return inline_keyboard(("⬅️ Назад", "user_main_menu"), ("💳 Оплатити", "consult:pay"))


async def eligible_user(event, services):
    user = services.user.get_user_by_tg_id(event.from_user.id)
    if user is None:
        return None
    if services.therapy.get_active_therapy_by_user_id(user.id) is not None:
        return None
    return user


@router.message(StateFilter(None), F.text.in_({"👩‍⚕️ Зв’язатися з лікарем", "👩‍⚕️ Консультація з лікарем"}))
async def contact_doctor(message: Message, services: Services):
    user = services.user.get_user_by_tg_id(message.from_user.id)
    if user is None:
        await message.answer("Будь ласка, спочатку пройдіть реєстрацію через /start.")
        return
    if services.therapy.get_active_therapy_by_user_id(user.id) is None:
        await message.answer(CONSULTATION_OFFER_TEXT, parse_mode="HTML", reply_markup=offer_keyboard())
        return
    await message.answer(
        f'👩‍⚕️ <b>Зв’язатися з лікарем</b>\n\n'
       "Якщо у вас виникли запитання щодо терапії, самопочуття або рекомендацій, ви можете звернутися безпосередньо до лікаря.\n\n"
        "<i>Не соромтеся ставити запитання — важливо, щоб на кожному етапі терапії ви почувалися впевнено та мали необхідну підтримку</i> 🤍\n"
        f'👉 <a href="{DOCTOR_URL}">Профіль лікаря</a>',
        parse_mode="HTML", reply_markup=keyboard
    )

@router.callback_query(F.data == "consult:back")
async def consultation_back(query: CallbackQuery, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    user = services.user.get_user_by_tg_id(query.from_user.id)
    if user and services.therapy.get_active_therapy_by_user_id(user.id) is not None:
        await query.message.edit_text(
            f'👉 <a href="{escape(DOCTOR_URL, quote=True)}">Профіль лікаря</a>',
            parse_mode="HTML", reply_markup=inline_keyboard(("⬅️ Назад", "user_main_menu")))
    else:
        await query.message.edit_text(CONSULTATION_OFFER_TEXT, parse_mode="HTML", reply_markup=offer_keyboard())


@router.callback_query(F.data == "consult:pay")
async def consultation_pay(query: CallbackQuery, services: Services):
    user = await eligible_user(query, services)
    if user is None:
        await query.answer("Поверніться до головного меню та відкрийте консультацію знову.", show_alert=True)
        return
    if not PAYMENT_IBAN or not PAYMENT_RECIPIENT:
        await query.answer("Реквізити тимчасово недоступні. Спробуйте пізніше.", show_alert=True)
        return
    await query.answer()
    if not isinstance(query.message, Message):
        return
    request = get_or_create_request(user.id)
    if request['status'] == 'pending':
        await query.message.edit_text(CONSULTATION_PENDING_TEXT, reply_markup=inline_keyboard(("⬅️ Назад", "user_main_menu")))
        return
    text = (
        "💳 <b>Оплата консультації — 500 грн</b>\n\n"
        f"<b>Отримувач:</b>\n{escape(PAYMENT_RECIPIENT)}\n\n"
        f"<b>IBAN:</b>\n<code>{escape(PAYMENT_IBAN)}</code>\n\n"
        f"<b>Призначення платежу:</b>\n{escape(PAYMENT_PURPOSE)}\n\n"
        "Після оплати натисніть кнопку <b>«Сплачено»</b> — лікар отримає повідомлення та зв’яжеться з вами."
    )
    if PAYMENT_TEST_MODE:
        text = "🧪 <b>Тестовий режим — не здійснюйте оплату.</b>\n\n" + text
    await query.message.edit_text(text, parse_mode="HTML", reply_markup=inline_keyboard(
        ("⬅️ Назад", "consult:back"), ("✅ Сплачено", f"consult:paid:{request['id']}")))


@router.callback_query(F.data.startswith("consult:paid:"))
async def consultation_paid(query: CallbackQuery, services: Services):
    user = await eligible_user(query, services)
    request_id = query.data.rsplit(":", 1)[-1]
    request = get_request(int(request_id)) if request_id.isdigit() else None
    if user is None or request is None or request['user_id'] != user.id:
        await query.answer("Ця заявка недоступна. Відкрийте консультацію з головного меню.", show_alert=True)
        return
    if not change_status(request['id'], 'payment', 'pending'):
        await query.answer("Вашу заявку вже передано лікарю.", show_alert=True)
        return
    delivered = False
    try:
        for doctor_id in DOCTOR_ID:
            await query.bot.send_message(
                doctor_id,
                f"🩺 <b>Оплата консультації №{request['id']}</b>\n\n"
                f'<a href="tg://user?id={user.tg_id}">{escape(user.full_name)}</a>\n'
                f"Телефон: {escape(user.phone)}\nTelegram ID: <code>{user.tg_id}</code>\n\n"
                "Клієнт повідомив про оплату <b>500 грн</b>. Перевірте надходження коштів.",
                parse_mode="HTML", reply_markup=inline_keyboard(
                    ("✅ Підтвердити оплату", f"consult:confirm:{request['id']}")))
            delivered = True
    except Exception:
        logging.exception("Could not notify doctor about consultation %s", request['id'])
        if not delivered:
            change_status(request['id'], 'pending', 'payment')
            await query.answer("Не вдалося повідомити лікаря. Спробуйте ще раз.", show_alert=True)
            return
    await query.answer()
    if isinstance(query.message, Message):
        await query.message.edit_text(CONSULTATION_PENDING_TEXT, reply_markup=inline_keyboard(("⬅️ Назад", "user_main_menu")))


@router.callback_query(F.data.startswith("consult:confirm:"))
async def consultation_confirm(query: CallbackQuery):
    if query.from_user.id not in DOCTOR_ID:
        await query.answer("Підтвердження доступне лише лікарю.", show_alert=True)
        return
    request_id = query.data.rsplit(":", 1)[-1]
    request = get_request(int(request_id)) if request_id.isdigit() else None
    if request is None or not change_status(request['id'], 'pending', 'confirmed'):
        await query.answer("Заявку вже оброблено або вона недоступна.", show_alert=True)
        return
    try:
        await query.bot.send_message(
            request['tg_id'], CONSULTATION_CONFIRMED_TEXT, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="👩‍⚕️ Профіль лікаря", url=DOCTOR_URL)
            ]]))
    except Exception:
        change_status(request['id'], 'confirmed', 'pending')
        logging.exception("Could not deliver consultation confirmation %s", request['id'])
        await query.answer("Не вдалося повідомити клієнта. Спробуйте ще раз.", show_alert=True)
        return
    await query.answer("Оплату підтверджено. Клієнта повідомлено.")
    if isinstance(query.message, Message):
        await query.message.edit_reply_markup(reply_markup=None)
