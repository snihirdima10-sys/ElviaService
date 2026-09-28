from datetime import datetime, date

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from app.database.repositories.therapy_repository import therapy_repository
from app.database.repositories.user_repository import user_repository
from app.utils.formatter import format_weeks

router = Router()


def get_therapy_history_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Головне меню")]
        ], resize_keyboard=True)

@router.message(StateFilter(None), F.text == "📋 Історія терапії")
async def therapy_history(message: Message):
    if message.from_user is None:
        return

    tg_id = int(message.from_user.id)


    if date is None:
        await message.answer("<b>💉 Історія дозувань</b>\n\n"
                             "У вас поки немає завершених періодів дозування.\n\n"
                             "Після призначення терапії тут відображатимуться\n:"
                             "• назва препарату та дозування;\n"
                             "• дати початку й завершення;\n"
                             "• тривалість приймання;\n"
                             "• зміна ваги за кожний період.\n\n"
                             "👩‍⚕️ Щоб розпочати терапію, пройдіть анкету та дочекайтеся консультації лікаря.")
        return

    user = user_repository.get_by_tg_id(tg_id)
    active_therapy =therapy_repository.get_active_by_tg_id(tg_id)
    therapies = therapy_repository.get_history_by_tg_id(tg_id)


    if user is None:
        return

    if active_therapy is None:
        return

    if therapies is None:
        return

    medication = active_therapy["medication"]
    dose_value = active_therapy["dose_value"]
    start_date = datetime.strptime(active_therapy["start_date"], "%Y-%m-%d").date()
    weeks = (date.today() - start_date).days // 7
    start_weight = active_therapy["start_weight"]
    current_weight = active_therapy["current_weight"]
    result_weight = round(start_weight - current_weight,1)

    active_dose_text = (
        "✅ <b>Поточний етап</b>\n\n"
        f"<b>{medication} • {dose_value} мг</b>\n\n"
        f"Початок: {start_date.strftime("%d.%m.%Y")}\n"
        f"Тривалість: {format_weeks(weeks)}\n"
        f"Актуальна вага: {user["current_weight"]} кг\n\n"
        f"──────────────\n\n"
        f"🌿 <b>Завершені етапи</b>\n\n"

    )

    history_therapy_text = ""

    for therapy in therapies:

        medication = therapy["medication"]
        dose_value = therapy["dose_value"]
        start_date = datetime.strptime(therapy["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(therapy["end_date"], "%Y-%m-%d").date()
        weeks = (date.today() - start_date).days // 7
        start_weight = therapy["start_weight"]
        end_weight = therapy["end_weight"]
        result_weight = round(start_weight - end_weight,1)

        history_therapy_text += (
            f"<b>{medication} • {dose_value} мг</b>\n\n"
            f"Період: {start_date.strftime("%d.%m")}–{end_date.strftime("%d.%m.%Y")}\n"
            f"Тривалість: {format_weeks(weeks)}\n"
            f"Вага: {start_weight} → {end_weight} кг\n"
            f"Результат: <b>{result_weight} кг</b>\n"
            f"──────────────\n"
        )

    overall_result = (
        "\n📊 <b>Загальний результат терапії</b>\n\n"
        f"Початкова вага: {start_weight} кг\n"
        f"Актуальна вага: {current_weight} кг\n"
        f"Зміна ваги: <b>{result_weight} кг</b>\n"
        f"Тривалість терапії: {format_weeks(weeks)}\n\n"
        "♻️️ <i>Зміна дозування можлива лише після погодження з лікарем</i>"
    )


    await message.answer(
        "👤 <b>Історія терапії</b>\n\n"
        "Тут зберігаються всі етапи терапії, зміни дозування та динаміка ваги\n\n"
        + active_dose_text + history_therapy_text + overall_result
        , reply_markup=get_therapy_history_keyboard()
    )