from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.container import Services
from app.handlers.admin.user_card import show_user_card
from app.states.admin.AdminState import AdminState

router = Router()
PAGE_SIZE = 10


async def show_users(event: Message | CallbackQuery, state: FSMContext, services: Services, page: int):
    users, total, page = services.user.get_users_page(page, PAGE_SIZE)
    await state.clear()
    await state.set_state(AdminState.wait_for_select_patient)
    await state.update_data(users_page=page)
    rows = [[InlineKeyboardButton(
        text=f"{user['full_name']} · {user['phone']}", callback_data=f"admin_user:{user['id']}"
    )] for user in users]
    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        navigation.append(InlineKeyboardButton(text="Далі ➡️", callback_data=f"admin_users:{page + 1}"))
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text="🏠 Панель лікаря", callback_data="admin_main_menu")])
    text = "👥 <b>Усі користувачі</b>\n\n"
    text += (f"Усього: <b>{total}</b>\nСторінка {page + 1} з {(total + PAGE_SIZE - 1) // PAGE_SIZE}\n\n"
             "Оберіть користувача, щоб переглянути його картку." if total else "Користувачів поки немає.")
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    if isinstance(event, CallbackQuery):
        if isinstance(event.message, Message):
            await event.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=markup, parse_mode="HTML")


@router.message(F.text == "👥 Усі користувачі")
async def open_users(message: Message, state: FSMContext, services: Services):
    await show_users(message, state, services, 0)


@router.callback_query(F.data.startswith("admin_users:"))
async def users_page(query: CallbackQuery, state: FSMContext, services: Services):
    value = query.data.split(":", 1)[1]
    if not value.isdecimal():
        await query.answer("Некоректна сторінка")
        return
    await query.answer()
    await show_users(query, state, services, int(value))


@router.callback_query(F.data.startswith("admin_user:"))
async def open_user(query: CallbackQuery, state: FSMContext, services: Services):
    value = query.data.split(":", 1)[1]
    user = services.user.get_by_user_id(int(value)) if value.isdecimal() else None
    if user is None:
        await query.answer("Користувача не знайдено", show_alert=True)
        return
    await query.answer()
    await show_user_card(query, user, state, services.therapy)
