from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import TIMEZONE, activate_due_therapies, request_checkins


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
        request_checkins, "cron", hour=10, minute=0,
        id="daily_checkin_reminders", kwargs={"bot": bot},
        next_run_time=datetime.now(TIMEZONE),
    )
    return scheduler
