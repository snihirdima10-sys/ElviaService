from contextlib import closing
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from aiogram.types import Chat, Message

from app.database import init_db, connection
from app.database.repositories import consultation_repository as repository
from app.handlers.user import contact_doctor as handlers
from app.keyboards.welcome_keyboard import get_welcome_keyboard
from app.texts.consultation import CONSULTATION_OFFER_TEXT, CONSULTATION_CONFIRMED_TEXT


class ConsultationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        db = Path(self.temp.name) / "test.db"
        self.patch1 = patch.object(init_db, "DB_PATH", db)
        self.patch2 = patch.object(connection, "DB_PATH", db)
        self.patch1.start()
        self.patch2.start()
        self.addCleanup(self.patch1.stop)
        self.addCleanup(self.patch2.stop)
        init_db.init_db()
        init_db.init_db()
        with closing(connection.get_connection()) as conn, conn:
            conn.execute("INSERT INTO users (tg_id, full_name, phone, height, start_weight, current_weight, target_weight) VALUES (101, 'Test User', '123', 170, 80, 80, 70)")
        self.user = SimpleNamespace(id=1, tg_id=101, full_name="Test <User>", phone="123")
        self.services = SimpleNamespace(
            user=SimpleNamespace(get_user_by_tg_id=Mock(return_value=self.user)),
            therapy=SimpleNamespace(get_active_therapy_by_user_id=Mock(return_value=None)))
        self.message = Message(message_id=1, date=datetime.now(), chat=Chat(id=101, type="private"),
                               from_user={"id": 101, "is_bot": False, "first_name": "Test"})
        self.query = SimpleNamespace(message=self.message, from_user=SimpleNamespace(id=101),
                                     answer=AsyncMock(), bot=SimpleNamespace(send_message=AsyncMock()))

    def request(self):
        request = repository.get_or_create_request(1)
        self.query.data = f"consult:paid:{request['id']}"
        return request

    async def test_free_consultation_preserves_doctor_profile(self):
        self.services.therapy.get_active_therapy_by_user_id.return_value = object()
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await handlers.contact_doctor(self.message, self.services)
        self.assertIn("Профіль лікаря", answer.call_args.args[0])
        self.assertNotIn("500", answer.call_args.args[0])
        self.assertIs(answer.call_args.kwargs['reply_markup'], handlers.keyboard)

    async def test_paid_offer_has_only_back_and_pay(self):
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await handlers.contact_doctor(self.message, self.services)
        self.assertEqual(answer.call_args.args[0], CONSULTATION_OFFER_TEXT)
        self.assertEqual([r[0].callback_data for r in answer.call_args.kwargs['reply_markup'].inline_keyboard],
                         ['user_main_menu', 'consult:pay'])

    async def test_payment_details_use_config_and_persist_request(self):
        with patch.multiple(handlers, PAYMENT_IBAN="UA_TEST", PAYMENT_RECIPIENT="Test Recipient", PAYMENT_PURPOSE="Test Purpose", PAYMENT_TEST_MODE=False):
            with patch.object(Message, "edit_text", new_callable=AsyncMock) as edit:
                await handlers.consultation_pay(self.query, self.services)
        text = edit.call_args.args[0]
        for value in ('UA_TEST', 'Test Recipient', 'Test Purpose', '500'):
            self.assertIn(value, text)
        self.assertEqual(repository.get_or_create_request(1)['id'], 1)
        self.assertEqual(len(edit.call_args.kwargs['reply_markup'].inline_keyboard), 2)

    async def test_paid_notification_is_not_confirmation_and_is_idempotent(self):
        request = self.request()
        with patch.object(handlers, 'DOCTOR_ID', [999]), patch.object(Message, 'edit_text', new_callable=AsyncMock):
            await handlers.consultation_paid(self.query, self.services)
            await handlers.consultation_paid(self.query, self.services)
        self.assertEqual(self.query.bot.send_message.await_count, 1)
        self.assertEqual(self.query.bot.send_message.call_args.args[0], 999)
        self.assertIn('Test &lt;User&gt;', self.query.bot.send_message.call_args.args[1])
        self.assertEqual(repository.get_request(request['id'])['status'], 'pending')

    async def test_foreign_request_and_active_therapy_cannot_report_payment(self):
        request = self.request()
        self.user.id = 2
        await handlers.consultation_paid(self.query, self.services)
        self.user.id = 1
        self.services.therapy.get_active_therapy_by_user_id.return_value = object()
        await handlers.consultation_paid(self.query, self.services)
        self.query.bot.send_message.assert_not_awaited()
        self.assertEqual(repository.get_request(request['id'])['status'], 'payment')

    async def test_notification_failure_allows_retry(self):
        request = self.request()
        self.query.bot.send_message.side_effect = RuntimeError('send failed')
        with patch.object(handlers, 'DOCTOR_ID', [999]), patch.object(handlers.logging, 'exception'):
            await handlers.consultation_paid(self.query, self.services)
        self.assertEqual(repository.get_request(request['id'])['status'], 'payment')

    async def test_only_doctor_can_confirm_and_duplicate_is_ignored(self):
        request = self.request()
        repository.change_status(request['id'], 'payment', 'pending')
        self.query.data = f"consult:confirm:{request['id']}"
        with patch.object(handlers, 'DOCTOR_ID', [999]), patch.object(Message, 'edit_reply_markup', new_callable=AsyncMock):
            await handlers.consultation_confirm(self.query)
            self.query.bot.send_message.assert_not_awaited()
            self.query.from_user.id = 999
            await handlers.consultation_confirm(self.query)
            await handlers.consultation_confirm(self.query)
        self.assertEqual(self.query.bot.send_message.await_count, 1)
        self.assertEqual(self.query.bot.send_message.call_args.args, (101, CONSULTATION_CONFIRMED_TEXT))
        self.assertEqual(repository.get_request(request['id'])['status'], 'confirmed')

    async def test_confirmation_delivery_failure_allows_retry(self):
        request = self.request()
        repository.change_status(request['id'], 'payment', 'pending')
        self.query.data = f"consult:confirm:{request['id']}"
        self.query.from_user.id = 999
        self.query.bot.send_message.side_effect = RuntimeError('send failed')
        with patch.object(handlers, 'DOCTOR_ID', [999]), patch.object(handlers.logging, 'exception'):
            await handlers.consultation_confirm(self.query)
        self.assertEqual(repository.get_request(request['id'])['status'], 'pending')

    def test_welcome_button_follows_start(self):
        buttons = [row[0].callback_data for row in get_welcome_keyboard().inline_keyboard]
        self.assertEqual(len(buttons), 4)
        self.assertEqual(buttons[:2], ['start_registration', 'consultation_prices'])
