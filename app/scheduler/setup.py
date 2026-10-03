from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .jobs import TIMEZONE, activate_due_therapies, request_weight


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=TIMEZONE,
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600},
    )
    scheduler.add_job(
        activate_due_therapies, "interval", minutes=2,
        id="activate_due_therapies", next_run_time=datetime.now(TIMEZONE),
    )
    scheduler.add_job(
        request_weight, "cron", hour=10, minute=0,
        id="weekly_weight_reminders", kwargs={"bot": bot},
        next_run_time=datetime.now(TIMEZONE),
    )
    return scheduler
