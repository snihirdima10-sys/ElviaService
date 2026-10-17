import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, Chat
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from app.models.dose import Dose
from app.handlers.admin.change_dose import request_dose
from app.handlers.admin.delete_dose import show_doses
from app.states.admin.AdminState import AdminState


class DoseSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = FSMContext(MemoryStorage(), StorageKey(bot_id=1, chat_id=1, user_id=1))
        await self.state.set_state(AdminState.show_patient)
        await self.state.update_data(user_id=42)
        self.message = Message(message_id=1, date=datetime.now(), chat=Chat(id=1, type="private"))
        self.query = SimpleNamespace(message=self.message, answer=AsyncMock())
        self.services = SimpleNamespace(dose=SimpleNamespace(
            get_all_doses=lambda: [Dose(n, "Mounjaro", n / 2, n * 500) for n in range(2, 21)]))

    async def test_first_click_opens_all_doses_and_preserves_patient(self):
        with patch.object(Message, "edit_text", new_callable=AsyncMock) as edit:
            await request_dose(self.query, self.state, self.services)
        rows = edit.call_args.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(len(rows), 19)
        self.assertEqual(rows[3][0].text, "Mounjaro - 2,5 мг")
        self.assertEqual(rows[3][0].callback_data, "dose_id:5")
        self.assertEqual(await self.state.get_state(), AdminState.change_dose.state)
        self.assertEqual((await self.state.get_data())["user_id"], 42)

    async def test_failed_display_keeps_patient_state_for_retry(self):
        error = TelegramBadRequest(method=EditMessageText(text="test", chat_id=1, message_id=1), message="failed")
        with patch.object(Message, "edit_text", new_callable=AsyncMock, side_effect=error):
            with self.assertRaises(TelegramBadRequest):
                await request_dose(self.query, self.state, self.services)
        self.assertEqual(await self.state.get_state(), AdminState.show_patient.state)
        with patch.object(Message, "edit_text", new_callable=AsyncMock):
            await request_dose(self.query, self.state, self.services)
        self.assertEqual(await self.state.get_state(), AdminState.change_dose.state)

    async def test_admin_list_accepts_dose_objects(self):
        with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
            await show_doses(self.message, self.state, self.services)
        rows = answer.call_args.kwargs["reply_markup"].inline_keyboard
        self.assertEqual(rows[0][0].callback_data, "delete_dose:select:2")
        self.assertIn("Mounjaro", rows[0][0].text)
        self.assertEqual(len([r for r in rows if r[0].callback_data.startswith("delete_dose:select:")]), 10)
