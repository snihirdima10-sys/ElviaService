from aiogram import F, Router
from aiogram.fsm.context import FSMContext

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.states.admin.AdminState import AdminState
from utils.formatter import format_weeks


def get_order_status_keyboard(order: dict) -> InlineKeyboardMarkup:
    buttons = []

    if order["status"] == "NEW":
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Взяти в роботу",
                callback_data=f"order_status:{order['id']}:processed"
            )
        ])

    elif order["status"] == "processed":
        buttons.append([
            InlineKeyboardButton(
                text="✅ Завершити",
                callback_data=f"order_status:{order['id']}:completed"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_show_orders"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

router = Router()

# status = ["new", "processed", "completed"]

title = {
    "new" : "🆕 НОВІ ЗАМОВЛЕННЯ",
    "processed" : "🔄 ОПРАЦЬОВАНІ",
    "completed" : "✅ ЗАВЕРШЕНІ"
}

@router.message(F.text == "📦 Замовлення", AdminState.show_admin_panel)
async def get_category_orders(message:Message, state: FSMContext):
    new_orders = get_orders_by_status("NEW")
    processed_orders = get_orders_by_status("processed")
    completed_orders = get_orders_by_status("completed")

    await state.update_data(
        new_orders=new_orders,
        processed_orders=processed_orders,
        completed_orders=completed_orders
    )

    await show_category(message=message, state=state)


async def show_category(message: Message, state: FSMContext):
    data = await state.get_data()
    new_orders = data["new_orders"]
    processed_orders = data["processed_orders"]
    completed_orders = data["completed_orders"]


    inline_keyboard= InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🆕 Нові ({len(new_orders)})", callback_data="orders:new")],
            [InlineKeyboardButton(text=f"🔄 Опрацьовані ({len(processed_orders)})", callback_data="orders:processed")],
            [InlineKeyboardButton(text=f"✅ Завершені ({len(completed_orders)})", callback_data="orders:completed")],
            [InlineKeyboardButton(text=f"🏠 Головне меню", callback_data="back_to_main_menu")],
        ]
    )

    text = ("📦 ЗАМОВЛЕННЯ\n\n"
            "Оберіть статус, щоб переглянути замовлення:")

    await state.set_state(AdminState.show_category_orders)

    if data.get("message_id"):
        await message.edit_text(text, reply_markup=inline_keyboard)
        await state.update_data(message_id=[])
        return
    else:
        await message.answer(text, reply_markup=inline_keyboard)

@router.callback_query(F.data.startswith("orders:"), AdminState.show_category_orders)
async def get_orders(query: CallbackQuery, state: FSMContext):
    if query.data is None:
        return
    status = query.data.split(":")[1]
    await state.update_data(status=status)

    await show_orders(query=query, state=state)


async def show_orders(query: CallbackQuery, state: FSMContext):

    data = await state.get_data()

    status = data["status"]
    orders = data[f"{status}_orders"]

    builder = InlineKeyboardBuilder()

    for order in orders:
        builder.add(InlineKeyboardButton(text=f"{order["full_name"]}", callback_data=f"order:{order['id']}"))

    builder.add(InlineKeyboardButton(text="⬅️ До статусів замовлень", callback_data="back_to_show_category"))
    builder.adjust(1)
    inline_keyboard = builder.as_markup()

    text = (f"{title[status]}\n\n"
            "Оберіть пацієнта, щоб переглянути замовлення:")


    await query.message.edit_text(text, reply_markup=inline_keyboard)


@router.callback_query(F.data.startswith("order:"), AdminState.show_category_orders)
async def show_order(query: CallbackQuery):
    order_id = int(query.data.split(":")[1])
    order = get_order(order_id)
    if not order:
        return

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_show_orders")]
        ]
    )
    text = (f"📦 Замовлення #{order["id"]}\n"
            f"💉 Препарат: {order["medication"]}\n"
            f"⚖️ Дозування: {order["dose_value"]} мг\n"
            f"📅 Період: {format_weeks(order["weeks_count"])}\n"
            f"💳 Сума: {order["total_price"]} грн\n"
            f"👤 Одержувач: {order["full_name"]}\n"
            f"📱 Телефон: {order["user_phone"]}\n"
            f"📮 Доставка: {order["delivery_data"]}")

    await query.message.edit_text(text, reply_markup=get_order_status_keyboard(order))

@router.callback_query(F.data =="back_to_show_category")
async def back_to_show_category(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.update_data(message_id=query.message.message_id)
    await show_category(query.message, state=state)

@router.callback_query(F.data == "back_to_show_orders")
async def back_to_show_orders(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await show_orders(query=query, state=state)


@router.callback_query(F.data.startswith("order_status:"))
async def change_order_status(query: CallbackQuery, state: FSMContext):
    await query.answer()

    if query.data is None:
        return

    _, order_id, new_status = query.data.split(":", 2)

    order_id = int(order_id)
    ALLOWED_ORDER_STATUSES = {"new", "processed", "completed"}
    if new_status not in ALLOWED_ORDER_STATUSES:
        await query.answer("Некоректний статус", show_alert=True)
        return

    order = get_order(order_id)

    if order is None:
        await query.answer("Замовлення не знайдено", show_alert=True)
        return