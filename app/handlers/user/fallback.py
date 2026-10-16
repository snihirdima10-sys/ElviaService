"""Registered last so valid user and administrator handlers run first."""
from aiogram import Router
from aiogram.types import Message, CallbackQuery

router = Router()
RECOVERY_TEXT = "Поточний крок або кнопка більше неактивні. Надішліть /start, щоб повернутися до головного меню."


@router.message()
async def unhandled_message(message: Message):
    if message.chat.type == "private":
        await message.answer(RECOVERY_TEXT)


@router.callback_query()
async def unhandled_callback(query: CallbackQuery):
    await query.answer("Кнопка більше неактивна. Надішліть /start.", show_alert=True)
    if isinstance(query.message, Message) and query.message.chat.type == "private":
        await query.message.answer(RECOVERY_TEXT)
