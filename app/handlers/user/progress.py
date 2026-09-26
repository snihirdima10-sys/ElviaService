from datetime import date, datetime

from aiogram import F
from aiogram.types import Message, BufferedInputFile
from aiogram import Router
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from app.database.service import get_user_by_id, get_first_therapy_date


def calculate_bmi(weight: float, height: float) -> float:
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def format_weeks(weeks: int) -> str:
    if weeks % 10 == 1 and weeks % 100 != 11:
        word = "тиждень"
    elif weeks % 10 in [2, 3, 4] and weeks % 100 not in [12, 13, 14]:
        word = "тижні"
    else:
        word = "тижнів"

    return f"{weeks} {word}"


router = Router()


@router.message(F.text == "📊 Мій прогрес")
async def progress(message: Message):
    if message.from_user is None:
        return

    tg_id = int(message.from_user.id)

    start_date = get_first_therapy_date(tg_id)

    if start_date is None:
        await message.answer("📊 Мій прогрес\n\n"
                             "Прогрес поки що не відображається.\n"
                             "Для початку відстеження необхідне щонайменше "
                             "одне призначення терапії від лікаря.")
        return

    data = get_user_by_id(tg_id)
    if data is None:
        return

    start_weight = data["start_weight"]
    current_weight = data["current_weight"]
    target_weight = data["target_weight"]
    height = data["height"]

    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
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

    width = 1080
    height = 1350

    # Координати для шаблону 1198x1313
    RESULT_POS = (width // 2, 514 + 50)
    START_WEIGHT_POS = (160 + 105, 800 + 50)
    CURRENT_WEIGHT_POS = (485 + 105, 800 + 50)
    GOAL_WEIGHT_POS = (810 + 105, 800 + 50)
    BMI_POS = (175 + 180, 980 + 50)
    THERAPY_WEEKS_POS = (660 + 180, 980 + 50)



    # Додаємо дані на картинку
    draw.text(
        RESULT_POS,
        f"{result:.1f} кг",
        font=font_result,
        fill=(70, 90, 60),
        anchor="mm"
    )

    draw.text(
        START_WEIGHT_POS,
        f"{start_weight:.1f} кг",
        font=font_medium,
        fill=(75, 55, 45),
        anchor="mm"
    )

    draw.text(
        CURRENT_WEIGHT_POS,
        f"{current_weight:.1f} кг",
        font=font_medium,
        fill=(75, 55, 45),
        anchor="mm"
    )

    draw.text(
        GOAL_WEIGHT_POS,
        f"{target_weight:.1f} кг",
        font=font_medium,
        fill=(75, 55, 45),
        anchor="mm"
    )

    draw.text(
        BMI_POS,
        f"{start_bmi:.1f} → {current_bmi:.1f}",
        font=font_medium,
        fill=(75, 55, 45),
        anchor="mm"
    )

    draw.text(
        THERAPY_WEEKS_POS,
        f"{weeks}",
        font=font_medium,
        fill=(75, 55, 45),
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
        caption="📊 Ваш актуальний прогрес"
    )