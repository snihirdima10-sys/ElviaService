from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.states.admin.AdminState import AdminState
from app.container import Services
from app.utils.formatter import format_weeks

router = Router()
STATUS_LABELS = {"new": "Нове", "processed": "Оброблено", "completed": "Завершено"}
PAGE_SIZE = 10


def category_keyboard():
    rows = [[InlineKeyboardButton(text="Усі замовлення", callback_data="admin_orders:all:0")]]
    for status, label in STATUS_LABELS.items():
        rows.append([InlineKeyboardButton(text=label, callback_data=f"admin_orders:{status}:0")])
    rows.append([InlineKeyboardButton(text="🏠 Панель лікаря", callback_data="admin_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.in_({"📦 Замовлення", " 📦 Замовлення"}))
async def get_category_orders(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminState.show_category_orders)
    await message.answer("📦 Замовлення\n\nОберіть статус:", reply_markup=category_keyboard())


@router.callback_query(F.data == "admin_order_categories", AdminState.show_category_orders)
async def show_categories(query: CallbackQuery):
    await query.answer()
    if isinstance(query.message, Message):
        await query.message.edit_text("📦 Замовлення\n\nОберіть статус:", reply_markup=category_keyboard())


async def show_orders(query: CallbackQuery, state: FSMContext, services: Services):
    if not isinstance(query.message, Message):
        return
    data = await state.get_data()
    status = data.get("order_filter", "all")
    orders = services.order.get_admin_orders(None if status == "all" else status)
    page = min(data.get("order_page", 0), max(0, (len(orders) - 1) // PAGE_SIZE))
    await state.update_data(order_page=page)
    rows = []
    for order in orders[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        rows.append([InlineKeyboardButton(
            text=f"№{order['id']} — {order['full_name']} — {STATUS_LABELS[order['status']]}",
            callback_data=f"admin_order:{order['id']}")])
    navigation = []
    if page > 0:
        navigation.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_orders:{status}:{page - 1}"))
    if (page + 1) * PAGE_SIZE < len(orders):
        navigation.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_orders:{status}:{page + 1}"))
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text="⬅️ До фільтрів", callback_data="admin_order_categories")])
    title = STATUS_LABELS.get(status, "Усі замовлення")
    text = f"📦 {title}\n\n" + (f"Оберіть замовлення. Сторінка {page + 1}." if orders else "Замовлень поки немає.")
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("admin_orders:"), AdminState.show_category_orders)
async def filter_orders(query: CallbackQuery, state: FSMContext, services: Services):
    _, status, page_text = query.data.split(":")
    if status not in {*STATUS_LABELS, "all"} or not page_text.isdecimal():
        await query.answer("Невідомий фільтр", show_alert=True)
        return
    await query.answer()
    await state.update_data(order_filter=status, order_page=int(page_text))
    await show_orders(query, state, services)


async def show_order(query: CallbackQuery, order: dict):
    rows = [[InlineKeyboardButton(text=f"Змінити на: {label}",
              callback_data=f"admin_order_status:{order['id']}:{status}")]
            for status, label in STATUS_LABELS.items() if status != order["status"]]
    rows.append([InlineKeyboardButton(text="⬅️ До списку", callback_data="admin_orders_back")])
    text = (
        f"📦 <b>Замовлення №{order['id']}</b>\n\n"
        f"Статус: <b>{STATUS_LABELS[order['status']]}</b>\n"
        f"Препарат: {escape(order['medication'])} · {order['dose_value']} мг\n"
        f"Період: {format_weeks(order['weeks_count'])}\n"
        f"Сума: {order['total_price']:.2f} грн\n"
        f"Дата: {escape(order['created_at'])}\n\n"
        f"Одержувач: {escape(order['full_name'])}\n"
        f"Телефон: {escape(order['user_phone'])}\n"
        f"Доставка: {escape(order['delivery_data'])}"
    )
    if isinstance(query.message, Message):
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("admin_order:"), AdminState.show_category_orders)
async def open_order(query: CallbackQuery, services: Services):
    order = services.order.get_admin_order(int(query.data.split(":")[1]))
    if order is None:
        await query.answer("Замовлення не знайдено", show_alert=True)
        return
    await query.answer()
    await show_order(query, order)


@router.callback_query(F.data == "admin_orders_back", AdminState.show_category_orders)
async def back_to_orders(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    await show_orders(query, state, services)


@router.callback_query(F.data.startswith("admin_order_status:"), AdminState.show_category_orders)
async def change_order_status(query: CallbackQuery, services: Services):
    _, order_id, status = query.data.split(":")
    if status not in STATUS_LABELS:
        await query.answer("Некоректний статус", show_alert=True)
        return
    order = services.order.get_admin_order(int(order_id))
    if order is None:
        await query.answer("Замовлення не знайдено", show_alert=True)
        return
    if order["status"] == status:
        await query.answer("Цей статус уже встановлено")
        return
    if not services.order.update_status(int(order_id), status):
        await query.answer("Не вдалося змінити статус", show_alert=True)
        return
    await query.answer("Статус змінено")
    order["status"] = status
    await show_order(query, order)
