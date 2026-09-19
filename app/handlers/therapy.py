from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from app.database.service import get_active_dose_by_user_id, get_user_dose_history, get_user_by_id
from datetime import datetime, date

router = Router()

def format_weeks(weeks: int) -> str:
    if weeks % 10 == 1 and weeks % 100 != 11:
        word = "тиждень"
    elif weeks % 10 in [2, 3, 4] and weeks % 100 not in [12, 13, 14]:
        word = "тижні"
    else:
        word = "тижнів"

    return f"{weeks} {word}"

@router.message(F.text == "🌿 Моя терапія")
async def therapy(message: Message):
    if message.from_user is None:
        return
    tg_id = int(message.from_user.id)

    data = get_active_dose_by_user_id(tg_id)

    if date is None:
        await message.answer("🌿 Ваша терапія\n\n"
                             "Наразі активну терапію не призначено.\n"
                             "Щоб розпочати терапію або отримати нове призначення, "
                             "зверніться до лікаря.\n\n"
                             "⚠Не починайте прийом препаратів і не змінюйте дозування самостійно.")
        return

    medication = data["medication"]
    dose_value = data["dose_value"]
    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
    weeks = (date.today() - start_date).days // 7

    text = (f"🌿 Ваша терапія\n\n"
            f"Препарат: {medication}\n"
            f"Актуальне дозування: {dose_value}\n"
            f"Початок терапії: {start_date}\n"
            f"Тривалість: {weeks}\n\n"
            f"⚠️ Не змінюйте дозування самостійно.")

    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Історія дозувань")],
        [KeyboardButton(text="🏠 Головне меню")],
    ], resize_keyboard=True)

    await message.answer(
        text,
    reply_markup=keyboard,)


@router.message(F.text == "📋 Історія дозувань")
async def therapy_history(message: Message):
    if message.from_user is None:
        return

    tg_id = int(message.from_user.id)

    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🏠 Головне меню")]
    ], resize_keyboard=True)

    if date is None:
        await message.answer("💉 Історія дозувань\n\n"
                             "У вас поки немає завершених періодів дозування.\n\n"
                             "Після призначення терапії тут відображатимуться\n:"
                             "• назва препарату та дозування;\n"
                             "• дати початку й завершення;\n"
                             "• тривалість приймання;\n"
                             "• зміна ваги за кожний період.\n\n"
                             "👩‍⚕️ Щоб розпочати терапію, пройдіть анкету та дочекайтеся консультації лікаря.")
        return

    data_dose = get_active_dose_by_user_id(tg_id)
    data_user = get_user_by_id(tg_id)

    if data_user is None:
        return

    if data_dose is None:
        return

    medication = data_dose["medication"]
    dose_value = data_dose["dose_value"]
    start_date = datetime.strptime(data_dose["start_date"], "%Y-%m-%d").date()
    weeks = (date.today() - start_date).days // 7
    weeks = format_weeks(weeks)
    start_weight = float(data_user["start_weight"])
    current_weight = float(data_user["current_weight"])
    result_weight = round(start_weight - current_weight,1)

    active_dose_text = ("🟢 Активне дозування\n\n"
                        f"{medication} — {dose_value} мг\n"
                        f"📅 Початок: {start_date}\n"
                        f"⏳ Тривалість: {weeks}\n"
                        f"⚖️ Вага: {start_weight} → {current_weight} кг\n"
                        f"📉 Результат: {result_weight} кг\n\n"
                        f"✅ Завершені дозування\n")

    history_doses_text = ""

    data_history_doses = get_user_dose_history(tg_id)
    if data_history_doses is None:
        return

    for item in data_history_doses:

        medication = item["medication"]
        dose_value = item["dose_value"]
        start_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
        weeks = (date.today() - start_date).days // 7
        weeks = format_weeks(weeks)
        start_weight = float(item["start_weight"])
        end_weight = float(item["end_weight"])
        result_weight = round(start_weight - end_weight,1)

        history_doses_text += (f"---------------------------------------\n"
                              f"{medication} — {dose_value} мг\n"
                              f"📅 {start_date}–{end_date}\n"
                              f"⏳ Тривалість: {weeks}\n"
                              f"⚖️ Вага: {start_weight} → {end_weight} кг\n"
                              f"📉 Результат: {result_weight} кг\n")

    overall_result = ("---------------------------------------\n\n"
                      "📊 Загальний результат терапії\n\n"
                      f"Початкова вага: {start_weight} кг\n"
                      f"Актуальна вага: {current_weight} кг\n"
                      f"Загальний результат: {result_weight} кг\n"
                      f"Тривалість терапії: {weeks}\n\n"
                      "⚠️ Дозування змінюється лише після погодження з лікарем.")


    await message.answer("💉 Історія дозувань\n\n"
                         "Тут зберігається історія змін вашого дозування "
                         "та результат за кожний період терапії.\n\n" + active_dose_text + history_doses_text + overall_result,
        reply_markup=keyboard,
    )