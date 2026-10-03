from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config import DOCTOR_ID


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery | CallbackQuery) -> bool:
        return event.from_user.id in DOCTOR_ID