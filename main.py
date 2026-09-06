import asyncio

from aiogram import Bot, Dispatcher

from app.handlers.start import router as start_router
from app.handlers.questionnaire import router as questionnaire_router
from app.handlers.contact_doctor import router as contact_doctor_router
from config import BOT_TOKEN


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(questionnaire_router)
    dp.include_router(contact_doctor_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())