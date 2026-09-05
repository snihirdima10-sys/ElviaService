import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

from app.handlers.start import router as start_router


load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())