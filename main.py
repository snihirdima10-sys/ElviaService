import asyncio

from aiogram import Bot, Dispatcher

from app.handlers.start import router as start_router
from app.handlers.therapy import router as therapy_router
from app.handlers.questionnaire import router as questionnaire_router
from app.handlers.contact_doctor import router as contact_doctor_router
from app.handlers.useful_info import router as useful_info_router
from app.handlers.progress import router as progress_router
from config import BOT_TOKEN
from app.scheduler import request_weight
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.init_db import init_db
from app.handlers.update_weight import router as update_weight_router

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    init_db()
    dp.include_router(start_router)
    dp.include_router(therapy_router)
    dp.include_router(questionnaire_router)
    dp.include_router(contact_doctor_router)
    dp.include_router(useful_info_router)
    dp.include_router(progress_router)
    dp.include_router(update_weight_router)

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        request_weight,
        trigger="cron",
        hour=10,
        minute=00,
        kwargs={"bot": bot}
    )

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())