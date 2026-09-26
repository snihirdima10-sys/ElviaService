from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.database.repositories.user_repository import user_repository
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.handlers.user.registration import  start_registration


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌿 Розпочати", callback_data="start_registration")],
            [InlineKeyboardButton(text="Політика конфіденційності", callback_data="start")]
        ]
    )
    return keyboard

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    if message.from_user is None:
        return
    user = user_repository.get_by_tg_id(message.from_user.id)

    if user is None:
        welcome_text = ("🌿 <b>Вітаємо в Elvia</b>\n\n"
                        "Ваш персональний простір турботи, контролю та впевненого руху до бажаного результату.\n\n"
                        "Тут зібрано все необхідне для комфортного проходження терапії: актуальні призначення, динаміка ваги, нагадування, корисні матеріали та зв’язок зі спеціалістом.\n\n"
                        "Elvia допомагає бачити прогрес, дотримуватися плану та отримувати підтримку на кожному етапі.\n\n"
                        "<i>Розпочнімо з короткої реєстрації та заповнення медичної анкети</i>")

        await message.answer(welcome_text, reply_markup=get_welcome_keyboard())
        return

    await message.answer("🌿 <b>Вітаємо в Elvia</b>\n\n"
                        "Ваш персональний простір турботи, контролю та впевненого руху до бажаного результату."
                         , reply_markup=get_main_menu_keyboard())
