from datetime import date
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile

from utils.formatter import format_weeks
from utils.user import calculate_bmi

# Координати для шаблону 1198x1313
RESULT_POS = (1080 // 2 + 20, 514 + 100)
START_WEIGHT_POS = (160 + 108, 800 + 100)
CURRENT_WEIGHT_POS = (485 + 108 + 20, 800 + 100)
GOAL_WEIGHT_POS = (810 + 120 + 20, 800 + 100)
BMI_POS = (175 + 183, 980 + 100)
THERAPY_WEEKS_POS = (660 + 183+10, 980 + 100)


def generate_progress_photo(
        start_weight: float,
        current_weight: float,
        target_weight: float,
        height: float,
        start_date: date
    ) -> BufferedInputFile:


    result = round(current_weight - start_weight, 1)

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
        quality=90, )

    # Переміщуємо курсор на початок
    buffer.seek(0)
    return BufferedInputFile(
        buffer.getvalue(),
        filename="progress.png"
    )
