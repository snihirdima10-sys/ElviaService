from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.states.admin.AdminState import AdminState

router =  Router()


@router.message(Command("admin"))
async def show_admin_panel(message: Message, state: FSMContext):

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Знайти пацієнта")],
            [KeyboardButton(text=" 📦 Замовлення")]
        ], resize_keyboard=True
    )

    await state.set_state(AdminState.show_admin_panel)
    await message.answer("👨‍⚕️ ПАНЕЛЬ ЛІКАРЯ\n\nОберіть потрібний розділ:", reply_markup=keyboard)