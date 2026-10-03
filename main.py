import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


from config import BOT_TOKEN

from app.database.init_db import init_db
from app.scheduler import create_scheduler

from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router

from app.database.repositories.user_repository import UserRepository
from app.database.repositories.dose_repository import DoseRepository
from app.database.repositories.therapy_repository import TherapyRepository

from app.services.user_service import UserService
from app.services.therapy_service import TherapyService
from app.services.dose_service import DoseService
from container import Services
from database.repositories.order_repository import OrderRepository
from database.repositories.weight_repository import WeightRepository
from services.order_service import OrderService
from services.weight_service import WeightService


# from redis.asyncio import Redis
# from aiogram.fsm.storage.redis import RedisStorage

async def main():

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # redis = Redis.from_url("redis://127.0.0.1:6379/0")
    # storage = RedisStorage(redis=redis)

    user_repository = UserRepository()
    dose_repository = DoseRepository()
    therapy_repository = TherapyRepository()
    weight_repository = WeightRepository()
    order_repository = OrderRepository()

    therapy_service = TherapyService(
        user_repository= user_repository,
        dose_repository= dose_repository,
        therapy_repository= therapy_repository,
    )

    user_service = UserService(
        user_repository= user_repository,
    )

    dose_service = DoseService(
        dose_repository= dose_repository,
    )

    weight_service = WeightService(
        weight_repository= weight_repository,
    )

    order_service = OrderService(
        order_repository= order_repository,
        dose_repository= dose_repository
    )

    services =Services(
        user=user_service,
        dose=dose_service,
        therapy=therapy_service,
        weight=weight_service,
        order=order_service,
    )

    # dp = Dispatcher(storage=storage)
    dp = Dispatcher()

    dp["services"] = services
    dp["user_service"] = user_service
    dp["therapy_service"] = therapy_service
    dp["dose_service"] = dose_service


    dp.include_router(admin_router)
    dp.include_router(user_router)

    init_db()

    scheduler = create_scheduler(bot)
    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
