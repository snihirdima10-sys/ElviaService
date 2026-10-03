from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram import Router

from app.keyboards.main_menu_keyboard import get_main_menu_keyboard

from container import Services
from utils.generate_progress_photo import generate_progress_photo


router = Router()


@router.message(StateFilter(None), F.text == "📊 Мій прогрес")
async def progress(message: Message, services: Services):
    if message.from_user is None:
        return
    tg_id = message.from_user.id
    user_id = services.user.get_user_id_by_tg_id(tg_id)
    if user_id is None:
        await message.answer("Спочатку зареєструйтеся за допомогою /start.")
        return

    active_therapy = services.therapy.get_active_therapy_by_user_id(user_id)
    stages = list(services.therapy.get_history_therapy_by_user_id(user_id) or [])
    if active_therapy:
        stages.append(active_therapy)
    if not active_therapy:
        await message.answer(
            "📊 Мій прогрес\n\n"
            "Прогрес поки що не відображається.\n"
            "Для початку відстеження необхідне щонайменше "
            "одне призначення терапії від лікаря."
        , reply_markup=get_main_menu_keyboard())
        return

    start_date = min(stage.start_date for stage in stages)
    user = services.user.get_by_user_id(user_id)
    if user is None:
        await message.answer("Не вдалося знайти ваші дані. Спробуйте /start.")
        return

    # Відправляємо картинку користувачу
    await message.answer_photo(
        photo=generate_progress_photo(
        start_weight=user.start_weight,
        current_weight= user.current_weight,
        target_weight=user.target_weight,
        height=user.height,
        start_date=start_date
        ),
    caption="📊 Ваш актуальний прогрес",
    reply_markup=get_main_menu_keyboard()
    )
