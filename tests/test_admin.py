from contextlib import closing
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock


import unittest
import test_scheduler
from app.database.repositories import order_repository as order_module
from app.database.repositories import therapy_repository as therapy_module
from app.database.repositories import user_repository as user_module
from app.services.order_service import OrderService
from app.texts.admin import format_user_card, format_therapies_history
from app.handlers.admin import user_orders
from aiogram.types import Message, Chat


class AdminTests(unittest.IsolatedAsyncioTestCase):
    setUp = test_scheduler.SchedulerTests.setUp
    connect = test_scheduler.SchedulerTests.connect

    async def test_order_filters_status_and_card(self):
        with patch.object(order_module, 'get_connection', self.connect):
            repository = order_module.OrderRepository()
            service = OrderService(repository, None)
            first = repository.create(1, 1, 1, 0, 100, 'Київ <центр>', 'new')
            repository.create(2, 1, 1, 0, 100, 'Львів', 'completed')
            self.assertEqual(len(service.get_admin_orders()), 2)
            self.assertEqual(len(service.get_admin_orders('new')), 1)
            self.assertEqual(service.get_admin_orders('processed'), [])
            self.assertTrue(service.update_status(first, 'processed'))
            self.assertEqual(service.get_admin_orders('new'), [])
            self.assertEqual(service.get_admin_order(first)['user_phone'], '123')
            with self.assertRaises(ValueError):
                service.update_status(first, 'invalid')
            message = Message(message_id=1, date=date.today(), chat=Chat(id=1, type='private'))
            query = SimpleNamespace(message=message)
            with patch.object(Message, 'edit_text', new_callable=AsyncMock) as edit:
                await user_orders.show_order(query, service.get_admin_order(first))
                self.assertIn('Оброблено', edit.call_args.args[0])
                self.assertIn('&lt;центр&gt;', edit.call_args.args[0])

    async def test_therapy_creation_and_patient_texts(self):
        with patch.object(therapy_module, 'get_connection', self.connect), patch.object(user_module, 'get_connection', self.connect):
            repository = therapy_module.TherapyRepository()
            new_id = repository.create_therapy(1, 1, date.today().isoformat(), 90, 'active')
            active = repository.get_active_by_user_id(1)
            self.assertEqual(active.id, new_id)
            history = repository.get_history_by_user_id(1)
            self.assertEqual(len(history), 1)
            from dataclasses import asdict
            user = asdict(user_module.UserRepository().get_by_id(1))
            self.assertIn('Test User', format_user_card(user, active, None))
            self.assertIn('Завершені етапи', format_therapies_history(user, active, history))
            repository.create_therapy(1, 1, (date.today()+timedelta(days=1)).isoformat(), 90, 'planned')
            repository.create_therapy(1, 1, (date.today()+timedelta(days=2)).isoformat(), 90, 'planned')
            with closing(self.connect()) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM therapies WHERE user_id=1 AND status='planned'").fetchone()[0], 1)
