from aiogram import Router
from aiogram.types import Message
from  aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards.back_menu import back_menu
from config import URL_GOOGLE_FORM


questionnaire_link_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📝 Заповнити анкету",
                url=URL_GOOGLE_FORM
            )
        ]
    ]
)

router = Router()

@router.message(F.text == "📝 Моя анкета")
async def questionnaire_handler(message: Message):
    await message.answer(
        "📝 Моя анкета:",
        reply_markup=back_menu
    )

    await message.answer("""
    Щоб лікар міг попередньо оцінити ваш стан і підготуватися до консультації, будь ласка, заповніть анкету за посиланням нижче.  
Вказуйте лише актуальну інформацію про стан здоров’я, препарати та попередній досвід терапії.  
Не надсилайте медичні дані звичайним повідомленням у чаті — використовуйте форму за посиланням.
    """, reply_markup=questionnaire_link_keyboard)