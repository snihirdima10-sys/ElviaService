from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.states.admin.AdminState import AdminState


# ===================================================KEYBOARDS===================================================

def get_admin_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Знайти пацієнта")],
            [KeyboardButton(text="👥 Усі користувачі")],
            [KeyboardButton(text="➕ Створити дозування")],
            [KeyboardButton(text="📦 Замовлення")]
        ], resize_keyboard=True
    )

# ==============================================================================================================


router =  Router()


@router.message(Command("admin"))
async def show_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminState.show_admin_panel)
    await message.answer("👨‍⚕️ ПАНЕЛЬ ЛІКАРЯ\n\nОберіть потрібний розділ:", reply_markup=get_admin_main_menu_keyboard())
