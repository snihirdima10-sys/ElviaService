from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.database.repositories.user_repository import user_repository
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.keyboards.privacy_policy_keyboard import get_privacy_policy_keyboard
from app.keyboards.welcome_keyboard import get_welcome_keyboard
from app.texts.privacy_policy import PRIVACY_POLICY_TEXT


WELCOME_TEXT = (
    "🌿 <b>Вітаємо в Elvia</b>\n\n"
    "Ваш персональний простір турботи, контролю та впевненого руху до бажаного результату.\n\n"
    "Тут зібрано все необхідне для комфортного проходження терапії: актуальні призначення, динаміка ваги, нагадування, корисні матеріали та зв’язок зі спеціалістом.\n\n"
    "Elvia допомагає бачити прогрес, дотримуватися плану та отримувати підтримку на кожному етапі.\n\n"
    "<i>Розпочнімо з короткої реєстрації та заповнення медичної анкети</i>"
    )


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    if message.from_user is None:
        return
    user = user_repository.get_by_tg_id(message.from_user.id)

    if user is None:
        await message.answer(WELCOME_TEXT, reply_markup=get_welcome_keyboard())
        return

    await message.answer("🌿 <b>Вітаємо в Elvia</b>\n\n"
                        "Ваш персональний простір турботи, контролю та впевненого руху до бажаного результату."
                         , reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "privacy_policy")
async def show_privacy_policy(callback: CallbackQuery):
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(PRIVACY_POLICY_TEXT, reply_markup=get_privacy_policy_keyboard())


@router.callback_query(F.data == "back_to_welcome_message")
async def back_to_welcome_message(callback: CallbackQuery):
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=get_welcome_keyboard())