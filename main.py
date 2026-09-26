import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from app.scheduler import request_weight
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database.init_db import init_db

from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    init_db()

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        request_weight,
        trigger="cron",
        hour=10,
        minute=00,
        kwargs={"bot": bot}
    )

    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())