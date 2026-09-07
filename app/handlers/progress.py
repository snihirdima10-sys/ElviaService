from aiogram import F
from aiogram.types import Message, BufferedInputFile
from aiogram import Router
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
router = Router()



@router.message(F.text == "📊 Мій прогрес")
async def progress(message: Message):

    start_weight = 92.0
    current_weight = 84.3
    goal_weight = 80.0
    result = -7.7
    start_bmi = 29.8
    current_bmi = 27.3
    therapy_weeks = 12

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
        f"{goal_weight:.1f} кг",
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
        f"{therapy_weeks} тижнів",
        font=font_medium,
        fill=(75, 55, 45),
        anchor="mm"
    )

    # Створюємо файл у пам'яті
    buffer = BytesIO()

    # Записуємо PNG у пам'ять, а не на диск
    image.save(buffer, format="PNG")

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