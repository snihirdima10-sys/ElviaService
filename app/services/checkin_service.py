"""Persistent check-in drafts and atomic, idempotent completion."""
import json
import math
from contextlib import closing
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.database.connection import get_connection


def today():
    return datetime.now(ZoneInfo('Europe/Kyiv')).date()


def decode(row):
    if row is None:
        return None
    result = dict(row)
    result['answers'] = json.loads(result['answers'])
    return result


class CheckinService:
    def __init__(self, connection_factory=None):
        self.connect = connection_factory or get_connection

    def get(self, user_id, checkin_id):
        with closing(self.connect()) as con:
            return decode(con.execute('SELECT * FROM weekly_checkins WHERE id=? AND user_id=?',
                                      (checkin_id, user_id)).fetchone())

    def draft(self, user_id):
        with closing(self.connect()) as con:
            return decode(con.execute("SELECT * FROM weekly_checkins WHERE user_id=? AND status='draft'",
                                      (user_id,)).fetchone())

    def begin(self, user_id, on=None, from_reminder=False):
        on = on or today()
        with closing(self.connect()) as con, con:
            con.execute('BEGIN IMMEDIATE')
            draft = con.execute("SELECT * FROM weekly_checkins WHERE user_id=? AND status='draft'", (user_id,)).fetchone()
            if draft:
                return decode(draft)
            last = con.execute("SELECT completed_at FROM weekly_checkins WHERE user_id=? AND status='completed' ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
            if last and on < datetime.fromisoformat(last['completed_at']).date() + timedelta(days=7):
                return None
            user = con.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            previous = con.execute('SELECT recorded_at FROM weight_history WHERE user_id=? ORDER BY recorded_at DESC, id DESC LIMIT 1', (user_id,)).fetchone()
            answers = dict(previous_weight=user['current_weight'], start_weight=user['start_weight'],
                           previous_date=previous['recorded_at'] if previous else user['created_at'])
            cursor = con.execute('INSERT INTO weekly_checkins(user_id, answers, last_reminded_on) VALUES (?, ?, ?)',
                                 (user_id, json.dumps(answers), None if from_reminder else on.isoformat()))
            return decode(con.execute('SELECT * FROM weekly_checkins WHERE id=?', (cursor.lastrowid,)).fetchone())

    def save(self, draft, step, answers):
        with closing(self.connect()) as con, con:
            return con.execute("UPDATE weekly_checkins SET step=?, answers=?, revision=revision+1 WHERE id=? AND user_id=? AND revision=? AND status='draft'",
                               (step, json.dumps(answers), draft['id'], draft['user_id'], draft['revision'])).rowcount == 1

    def complete(self, draft, on=None):
        on = on or today()
        with closing(self.connect()) as con, con:
            con.execute('BEGIN IMMEDIATE')
            current = decode(con.execute('SELECT * FROM weekly_checkins WHERE id=? AND user_id=?', (draft['id'], draft['user_id'])).fetchone())
            if not current or current['status'] != 'draft' or current['revision'] != draft['revision'] or current['step'] != 'review':
                return False
            a = current['answers']
            if not all(k in a for k in ('weight', 'wellbeing', 'appetite', 'reactions', 'dose')):
                raise ValueError('Incomplete check-in')
            weight = a['weight']
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or not 30 <= weight <= 400:
                raise ValueError('Вага обов’язкова: введіть коректне значення від 30 до 400 кг.')
            if a['reactions'] and (not a.get('symptoms') or ('other' in a['symptoms'] and not a.get('symptom_other'))):
                raise ValueError('Missing symptoms')
            if not a['dose'] and (not a.get('reason') or (a['reason'] == 'other' and not a.get('reason_other'))):
                raise ValueError('Missing dose reason')
            con.execute("UPDATE weekly_checkins SET status='completed', completed_at=?, revision=revision+1 WHERE id=?", (on.isoformat(), draft['id']))
            con.execute('INSERT INTO weight_history(user_id, weight) VALUES (?, ?)', (draft['user_id'], a['weight']))
            con.execute('UPDATE users SET current_weight=?, next_checkin_at=? WHERE id=?',
                        (a['weight'], (on + timedelta(days=7)).isoformat(), draft['user_id']))
            return True

    def history(self, user_id, offset=0):
        with closing(self.connect()) as con:
            return [decode(r) for r in con.execute("SELECT * FROM weekly_checkins WHERE user_id=? AND status='completed' ORDER BY completed_at DESC, id DESC LIMIT 6 OFFSET ?", (user_id, offset))]
