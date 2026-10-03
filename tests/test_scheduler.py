from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

for key in ("BOT_TOKEN", "URL_GOOGLE_FORM", "DOCTOR_URL", "CHANNEL_URL"):
    os.environ.setdefault(key, "test")
os.environ.setdefault("DOCTOR_ID", "1")

from app.database import init_db
from app.scheduler import jobs, create_scheduler


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "test.db"
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(patch.stopall)
        patch.object(jobs, "get_connection", self.connect).start()
        with patch.object(init_db, "get_connection", self.connect):
            init_db.init_db()
        with closing(self.connect()) as con, con:
            for user_id, due in ((1, '2026-10-03'), (2, '2026-10-04'), (3, '2026-10-01')):
                con.execute("""INSERT INTO users
                    (id, tg_id, full_name, phone, height, start_weight,
                     current_weight, target_weight, next_weight_request_at)
                    VALUES (?, ?, 'Test User', '123', 170, 100, 90, 80, ?)""",
                    (user_id, user_id, due))
            con.execute("INSERT INTO doses(id, medication, dose_value, price) VALUES(1, 'Test', 1, 1)")
            con.executemany("""INSERT INTO therapies
                (id, user_id, dose_id, start_date, start_weight, status)
                VALUES (?, ?, 1, ?, 100, ?)""", [
                (1, 1, '2026-09-01', 'active'),
                (2, 1, '2026-10-03', 'planned'),
                (3, 2, '2026-10-04', 'planned'),
                (4, 3, '2026-10-01', 'planned'),
            ])

    def connect(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        return con

    async def test_due_overdue_future_and_repeat_activation(self):
        self.assertEqual(await jobs.activate_due_therapies(date(2026, 10, 3)), 2)
        self.assertEqual(await jobs.activate_due_therapies(date(2026, 10, 3)), 0)
        with closing(self.connect()) as con, con:
            rows = con.execute('SELECT * FROM therapies ORDER BY id').fetchall()
        self.assertEqual([r['status'] for r in rows], ['completed', 'active', 'planned', 'active'])
        self.assertEqual(rows[0]['end_date'], '2026-10-03')
        self.assertEqual(rows[0]['end_weight'], 90)
        self.assertEqual(rows[1]['start_weight'], 90)

    async def test_transition_rolls_back_on_failure(self):
        with closing(self.connect()) as con, con:
            con.execute("""CREATE TRIGGER fail_activation BEFORE UPDATE OF status ON therapies
                WHEN NEW.status = 'active' BEGIN SELECT RAISE(ABORT, 'test'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            await jobs.activate_due_therapies(date(2026, 10, 3))
        with closing(self.connect()) as con, con:
            self.assertEqual(con.execute('SELECT status FROM therapies WHERE id=1').fetchone()[0], 'active')

    async def test_weekly_reminders_and_failed_delivery(self):
        bot = AsyncMock()
        bot.send_message.side_effect = [RuntimeError('unavailable'), None]
        with self.assertLogs(jobs.logger, level='ERROR'):
            self.assertEqual(await jobs.request_weight(bot, date(2026, 10, 3)), 1)
        with closing(self.connect()) as con, con:
            dates = [r[0] for r in con.execute('SELECT next_weight_request_at FROM users ORDER BY id')]
        self.assertEqual(dates, ['2026-10-03', '2026-10-04', '2026-10-10'])
        bot.send_message.side_effect = None
        self.assertEqual(await jobs.request_weight(bot, date(2026, 10, 3)), 1)
        self.assertEqual(await jobs.request_weight(bot, date(2026, 10, 3)), 0)
        self.assertEqual(await jobs.request_weight(bot, date(2026, 10, 10)), 3)

    async def test_scheduler_configuration(self):
        scheduler = create_scheduler(AsyncMock())
        scheduler.start(paused=True)
        try:
            self.assertEqual(len(scheduler.get_jobs()), 2)
            for job in scheduler.get_jobs():
                self.assertEqual(job.max_instances, 1)
                self.assertTrue(job.coalesce)
            self.assertEqual(str(scheduler.timezone), 'Europe/Kyiv')
        finally:
            scheduler.shutdown(wait=False)

