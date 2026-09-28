from datetime import date, datetime

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import Message, BufferedInputFile
from aiogram import Router
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from app.database.repositories.therapy_repository import therapy_repository
from app.database.repositories.user_repository import user_repository
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard
from app.utils.formatter import format_weeks


def calculate_bmi(weight: float, height: float) -> float:
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


# Координати для шаблону 1198x1313
RESULT_POS = (1080 // 2 + 20, 514 + 100)
START_WEIGHT_POS = (160 + 108, 800 + 100)
CURRENT_WEIGHT_POS = (485 + 108 + 20, 800 + 100)
GOAL_WEIGHT_POS = (810 + 120 + 20, 800 + 100)
BMI_POS = (175 + 183, 980 + 100)
THERAPY_WEEKS_POS = (660 + 183+10, 980 + 100)


router = Router()


@router.message(StateFilter(None), F.text == "📊 Мій прогрес")
async def progress(message: Message):
    if message.from_user is None:
        return

    tg_id = message.from_user.id
    therapy = therapy_repository.get_first_by_tg_id(tg_id)
    start_date = therapy["created_at"]

    if start_date is None:
        await message.answer(
            "📊 Мій прогрес\n\n"
            "Прогрес поки що не відображається.\n"
            "Для початку відстеження необхідне щонайменше "
            "одне призначення терапії від лікаря."
        )
        return

    user = user_repository.get_by_tg_id(tg_id)
    if user is None:
        return

    start_weight = user["start_weight"]
    current_weight = user["current_weight"]
    target_weight = user["target_weight"]
    height = user["height"]

    start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").date()
    result = round(float(current_weight) - float(start_weight), 1)

    start_bmi = calculate_bmi(start_weight, height)
    current_bmi = calculate_bmi(current_weight, height)

    weeks = (date.today() - start_date).days // 7
    weeks = format_weeks(weeks)

    # Відкриваємо шаблон
    image = Image.open("app/assets/progress_template_new.png").convert("RGB")

    draw = ImageDraw.Draw(image)

    # Підключаємо шрифти
    font_result = ImageFont.truetype("app/assets/fonts/BalsamiqSans-Bold.ttf", 80)
    font_medium = ImageFont.truetype("app/assets/fonts/BalsamiqSans-Regular.ttf", 42)

    # Додаємо дані на картинку
    draw.text(
        RESULT_POS,
        f"{result:.1f} кг",
        font=font_result,
        fill=(243, 201, 107),
        anchor="mm"
    )

    draw.text(
        START_WEIGHT_POS,
        f"{start_weight:.1f} кг",
        font=font_medium,
        fill=(243, 201, 107),
        anchor="mm"
    )

    draw.text(
        CURRENT_WEIGHT_POS,
        f"{current_weight:.1f} кг",
        font=font_medium,
        fill=(243, 201, 107),
        anchor="mm"
    )

    draw.text(
        GOAL_WEIGHT_POS,
        f"{target_weight:.1f} кг",
        font=font_medium,
        fill=(243, 201, 107),
        anchor="mm"
    )

    draw.text(
        BMI_POS,
        f"{start_bmi:.1f} → {current_bmi:.1f}",
        font=font_medium,
        fill=(243, 201, 107),
        anchor="mm"
    )

    draw.text(
        THERAPY_WEEKS_POS,
        f"{weeks}",
        font=font_medium,
        fill=(243, 201, 107),
        anchor="mm"
    )

    # Створюємо файл у пам'яті
    buffer = BytesIO()

    # Записуємо PNG у пам'ять, а не на диск
    image.save(
        buffer,
        format="JPEG",
        quality=90,)

    # Переміщуємо курсор на початок
    buffer.seek(0)

    # Перетворюємо байти на Telegram-файл
    photo = BufferedInputFile(
        buffer.getvalue(),
        filename="progress.png"
    )

    # Відправляємо картинку користувачу
    await message.answer_photo(
        photo=photo,
        caption="📊 Ваш актуальний прогрес",
        reply_markup=get_main_menu_keyboard()
    )