import asyncio

from aiogram import Bot, Dispatcher

from app.database.service import get_active_dose
from app.handlers.start import router as start_router
from app.handlers.questionnaire import router as questionnaire_router
from app.handlers.contact_doctor import router as contact_doctor_router
from app.handlers.useful_info import router as useful_info_router
from app.handlers.progress import router as progress_router
from config import BOT_TOKEN

from app.database.init_db import init_db


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    init_db()
    dp.include_router(start_router)
    dp.include_router(questionnaire_router)
    dp.include_router(contact_doctor_router)
    dp.include_router(useful_info_router)
    dp.include_router(progress_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())