from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.container import Services
from app.handlers.admin.user_card import show_user_card
from app.handlers.user.checkin import keyboard, summary, number, delta
from app.services.checkin_service import CheckinService
from app.states.admin.AdminState import AdminState
from app.utils.formatter import format_date

router = Router()
service = CheckinService()


@router.callback_query(F.data.startswith('checkins:'), AdminState.show_patient)
async def history(query: CallbackQuery, state: FSMContext, services: Services):
    await query.answer()
    if not isinstance(query.message, Message):
        return
    data = await state.get_data()
    user_id = data.get('user_id')
    if user_id is None:
        return
    parts = query.data.split(':')
    if parts[1] == 'card':
        user = services.user.get_by_user_id(user_id)
        if user:
            await show_user_card(query, user, state, services.therapy)
        return
    if len(parts) != 3 or not parts[2].isdigit():
        return
    value = int(parts[2])
    if parts[1] == 'view':
        result = service.get(user_id, value)
        if not result or result['status'] != 'completed':
            return
        await query.message.edit_text(f"📋 <b>Check-in від {format_date(result['completed_at'])}</b>\n\n" + summary(result['answers']),
                                      reply_markup=keyboard([('← До історії', f"checkins:page:{data.get('checkin_offset', 0)}"), ('Картка пацієнта', 'checkins:card')]))
    elif parts[1] == 'page':
        results = service.history(user_id, value)
        await state.update_data(checkin_offset=value)
        items = [(f"{format_date(r['completed_at'])} • {number(r['answers']['weight'])} кг • {delta(r['answers'])}", f"checkins:view:{r['id']}") for r in results[:5]]
        if value:
            items.append(('← Попередні', f'checkins:page:{max(0, value-5)}'))
        if len(results) > 5:
            items.append(('Наступні →', f'checkins:page:{value+5}'))
        items.append(('Картка пацієнта', 'checkins:card'))
        await query.message.edit_text('📋 <b>Результати check-in</b>\n\n' + ('Оберіть дату:' if results else 'Результатів поки немає.'), reply_markup=keyboard(items))
