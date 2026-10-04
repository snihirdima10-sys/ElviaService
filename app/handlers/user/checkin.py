from html import escape

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.container import Services
from app.services.checkin_service import CheckinService
from app.keyboards.main_menu_keyboard import get_main_menu_keyboard, CHECKIN_TEST_MENU
from app.utils.validators import is_valid_weight
from app.utils.formatter import format_date
from config import CHECKIN_TEST_BUTTON_ENABLED

router = Router()
service = CheckinService()
MENU = CHECKIN_TEST_MENU
INTRO = (
    '🌿 <b>Щотижневий check-in</b>\n\n'
    'Час приділити кілька хвилин вашому прогресу та самопочуттю.\n\n'
    'Check-in займе лише <b>1–2 хвилини</b> та допоможе нам краще відстежувати динаміку терапії й ваші зміни протягом тижня.\n\n'
    '<b>Почнемо?</b>'
)
COMPLETED = (
    '🌿 <b>Check-in завершено</b>\n\n'
    'Дякуємо! Ваші відповіді збережено.\n\n'
    'Наступний check-in буде доступний <b>через 7 днів</b> — ми надішлемо запрошення автоматично.\n\n'
    'До зустрічі на наступному check-in 🤍'
)
OPTIONS = {
    'wellbeing': {'good': '😊 Добре', 'normal': '🙂 Нормально', 'low': '😕 Не дуже', 'bad': '😣 Погано'},
    'appetite': {'much_less': '🔻 Значно зменшився', 'less': '↘️ Трохи зменшився', 'same': '➡️ Без змін', 'more': '↗️ Посилився'},
    'symptoms': {'nausea': 'Нудота', 'vomiting': 'Блювання', 'diarrhea': 'Діарея', 'constipation': 'Закреп', 'pain': 'Біль у животі', 'weakness': 'Слабкість', 'headache': 'Головний біль', 'other': 'Інше'},
    'reason': {'forgot': 'Забув(ла)', 'unwell': 'Погане самопочуття', 'unavailable': 'Не було препарату', 'doctor': 'За рекомендацією лікаря', 'other': 'Інша причина'},
}
PREVIOUS = {'confirm_weight': 'weight', 'wellbeing': 'weight', 'appetite': 'wellbeing', 'reactions': 'appetite',
            'symptoms': 'reactions', 'symptom_other': 'symptoms', 'dose': 'reactions', 'reason': 'dose',
            'reason_other': 'reason', 'measurements': 'dose', 'chest': 'measurements', 'waist': 'chest', 'hips': 'waist', 'review': 'measurements'}


class CheckinState(StatesGroup):
    active = State()


def keyboard(items):
    return InlineKeyboardMarkup(inline_keyboard=[
        *[[InlineKeyboardButton(text=t, callback_data=c)] for t, c in items],
        [InlineKeyboardButton(text="🏠 Головне меню", callback_data="user_main_menu")],
    ])


def intro_keyboard():
    return keyboard([('✨ Розпочати', 'ci:start')])


def number(value):
    return f'{value:.1f}'.replace('.', ',')


def delta(a):
    value = a['weight'] - a['previous_weight']
    return f'{value:+.1f}'.replace('.', ',').replace('-', '−') + ' кг'


def summary(a):
    symptoms = ', '.join(OPTIONS['symptoms'][s].lower() for s in a.get('symptoms', [])) if a['reactions'] else 'немає'
    if a.get('symptom_other') and a['reactions']:
        symptoms += ': ' + escape(a['symptom_other'])
    dose = 'підтверджено' if a['dose'] else 'не прийнято — ' + OPTIONS['reason'][a['reason']]
    if not a['dose'] and a.get('reason_other'):
        dose += ': ' + escape(a['reason_other'])
    return (f"⚖️ <b>Вага:</b> {number(a['weight'])} кг\n"
            f"📉 <b>Зміна з {format_date(a['previous_date'])}:</b> {delta(a)}\n"
            f"🌿 <b>Самопочуття:</b> {OPTIONS['wellbeing'][a['wellbeing']]}\n"
            f"🍽 <b>Апетит:</b> {OPTIONS['appetite'][a['appetite']]}\n"
            f"🩺 <b>Побічні реакції:</b> {symptoms}\n💉 <b>Прийом дози:</b> {dose}\n\n"
            '<b>Заміри тіла</b>\n' +
            '\n'.join(f"📏 {label}: " + (number(a[key]) + ' см' if a.get(key) is not None else 'не вказано')
                      for key, label in [('chest', 'Груди'), ('waist', 'Талія'), ('hips', 'Стегна')]) +
            f"\n\n✨ <b>Загальний результат: {a['weight'] - a['start_weight']:+.1f} кг</b>".replace('.', ',').replace('-', '−'))


def screen(d):
    a, step = d['answers'], d['step']
    items = []
    if step == 'weight':
        text = (
            '<b>1/6 ⚖️ Актуальна вага</b>\n\n'
            'Вкажіть вашу <b>актуальну вагу</b>, щоб ми могли відстежувати динаміку терапії.\n\n'
            f"Попереднє значення: <b>{number(a['previous_weight'])} кг</b>\n"
            'Введіть вагу в кг, наприклад: <b>66,4</b>\n\n'
            '🌿 Цей показник є важливою частиною check-in, тому його потрібно заповнити для продовження.'
        )
    elif step == 'confirm_weight':
        text = f"1/6 ✅ <b>{number(a['weight'])} кг</b>\nЗміна від попереднього вимірювання: {delta(a)}"
        items = [('Продовжити →', 'next')]
    elif step in ('wellbeing', 'appetite'):
        text = ('2/6 🌿 <b>Самопочуття</b>\n\nЯк ви оцінюєте своє самопочуття протягом останнього тижня?' if step == 'wellbeing' else
                '3/6 🍽 <b>Апетит</b>\n\nЯк змінився ваш апетит протягом останнього тижня?')
        items = [(v, k) for k, v in OPTIONS[step].items()]
    elif step in ('reactions', 'dose'):
        text = ('4/6 🩺 <b>Побічні реакції</b>\n\nЧи помічали ви небажані реакції або зміни самопочуття після останньої дози?' if step == 'reactions' else
                '5/6 💉 <b>Прийом призначеної дози</b>\n\nЧи була прийнята призначена доза цього тижня?')
        items = [('⚠️ Так' if step == 'reactions' else '✅ Так', 'yes'), ('✅ Ні' if step == 'reactions' else '❌ Ні', 'no')]
    elif step == 'symptoms':
        text = '4/6 🩺 Що саме вас турбувало?\nМожна обрати декілька варіантів.'
        items = [(('☑️ ' if k in a.get('symptoms', []) else '') + v, k) for k, v in OPTIONS['symptoms'].items()] + [('✅ Готово', 'done')]
    elif step == 'reason':
        text = '5/6 💉 Вкажіть, будь ласка, причину пропуску дози.'
        items = [(v, k) for k, v in OPTIONS['reason'].items()]
    elif step in ('symptom_other', 'reason_other'):
        text = ('4/6 Коротко опишіть симптом.' if step == 'symptom_other' else '5/6 Коротко опишіть причину.') + '\nДо 500 символів.'
    elif step == 'measurements':
        text = '6/6 📏 <b>Заміри тіла</b>\n\nНеобов’язковий етап: груди, талія, стегна.'
        items = [('Внести заміри', 'enter'), ('Пропустити', 'skip')]
    elif step in ('chest', 'waist', 'hips'):
        label = {'chest': 'грудей', 'waist': 'талії', 'hips': 'стегон'}[step]
        text = f'6/6 📏 Введіть обхват {label} у сантиметрах, наприклад: 95,5'
        items = [('Пропустити цей замір', 'skip')]
    else:
        text = 'Перевірте відповіді перед збереженням:\n\n' + summary(a)
        items = [('✅ Завершити та зберегти', 'finish')]
    if step in PREVIOUS:
        items.append(('← Назад', 'back'))
    return text, keyboard([(t, f"ci:{d['id']}:{d['revision']}:{action}") for t, action in items])


async def render(message, draft, edit=False):
    text, markup = screen(draft)
    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.message(F.text == MENU)
async def invitation(message: Message, state: FSMContext, services: Services):
    if not CHECKIN_TEST_BUTTON_ENABLED:
        return
    user = services.user.get_user_by_tg_id(message.from_user.id) if message.from_user else None
    if not user:
        await message.answer('Спочатку зареєструйтеся через /start.')
        return
    # Only this temporary testing entry point may create a manual invitation.
    if not service.begin(user.id):
        await message.answer(COMPLETED, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
        return
    await state.clear()
    await message.answer(INTRO, reply_markup=intro_keyboard())


@router.callback_query(F.data.startswith('ci:'))
async def action(query: CallbackQuery, state: FSMContext, services: Services):
    if not isinstance(query.message, Message):
        await query.answer()
        return
    user = services.user.get_user_by_tg_id(query.from_user.id)
    if not user:
        await query.answer('Спочатку зареєструйтеся через /start', show_alert=True)
        return
    if query.data == 'ci:start':
        # The scheduler creates the draft before delivering the invitation.
        # An old invitation must not create a new, unscheduled check-in.
        d = service.draft(user.id)
        if not d:
            await query.answer('Зараз немає відкритого опитування. Наступне запрошення надійде автоматично.', show_alert=True)
            return
        # Invalidate buttons from previous copies of the draft screen.
        service.save(d, d['step'], d['answers'])
        d = service.draft(user.id)
        await query.answer()
        await state.set_state(CheckinState.active)
        await render(query.message, d, edit=True)
        return
    parts = query.data.split(':')
    if len(parts) != 4 or not parts[1].isdigit() or not parts[2].isdigit():
        await query.answer()
        return
    d = service.get(user.id, int(parts[1]))
    if not d or d['status'] != 'draft' or d['revision'] != int(parts[2]):
        await query.answer('Ця кнопка вже неактуальна. Натисніть «Розпочати / продовжити» в останньому запрошенні.', show_alert=True)
        return
    a, step, choice = d['answers'].copy(), d['step'], parts[3]
    next_step = step
    if choice == 'back' and step in PREVIOUS:
        next_step = PREVIOUS[step]
    elif step == 'confirm_weight' and choice == 'next':
        next_step = 'wellbeing'
    elif step in ('wellbeing', 'appetite') and choice in OPTIONS[step]:
        a[step] = choice
        next_step = 'appetite' if step == 'wellbeing' else 'reactions'
    elif step in ('reactions', 'dose') and choice in ('yes', 'no'):
        a[step] = choice == 'yes'
        if step == 'reactions':
            if not a[step]:
                a.update(symptoms=[], symptom_other=None)
            next_step = 'symptoms' if a[step] else 'dose'
        else:
            if a[step]:
                a.update(reason=None, reason_other=None)
            next_step = 'measurements' if a[step] else 'reason'
    elif step == 'symptoms' and choice in OPTIONS['symptoms']:
        selected = list(a.get('symptoms', []))
        selected.remove(choice) if choice in selected else selected.append(choice)
        a['symptoms'] = selected
        if 'other' not in selected:
            a['symptom_other'] = None
    elif step == 'symptoms' and choice == 'done':
        if not a.get('symptoms'):
            await query.answer('Оберіть хоча б один симптом.', show_alert=True)
            return
        next_step = 'symptom_other' if 'other' in a['symptoms'] else 'dose'
    elif step == 'reason' and choice in OPTIONS['reason']:
        a.update(reason=choice, reason_other=None)
        next_step = 'reason_other' if choice == 'other' else 'measurements'
    elif step == 'measurements' and choice in ('enter', 'skip'):
        if choice == 'skip':
            a.update(chest=None, waist=None, hips=None)
        next_step = 'chest' if choice == 'enter' else 'review'
    elif step in ('chest', 'waist', 'hips') and choice == 'skip':
        a[step] = None
        next_step = {'chest': 'waist', 'waist': 'hips', 'hips': 'review'}[step]
    elif step == 'review' and choice == 'finish':
        if service.complete(d):
            await state.clear()
            await query.answer()
            await query.message.edit_text(
                '✅ <b>Check-in завершено</b>\n\nДякуємо! Ваші дані за цей тиждень збережено 🤍\n\n'
                + summary(a) + '\n\nНаступний check-in буде доступний через 7 днів. 🌿',
                parse_mode="HTML",
            )
            await query.message.answer('Головне меню:', reply_markup=get_main_menu_keyboard())
        else:
            await query.answer('Результат уже збережено або відповіді змінилися.')
        return
    else:
        await query.answer('Скористайтеся кнопками поточного етапу.')
        return
    if not service.save(d, next_step, a):
        await query.answer('Відповіді вже змінилися. Відкрийте check-in знову.')
        return
    await query.answer()
    await state.set_state(CheckinState.active)
    await render(query.message, service.draft(user.id), edit=True)


@router.message(StateFilter(CheckinState.active))
async def input_answer(message: Message, services: Services):
    if not message.from_user:
        return
    user = services.user.get_user_by_tg_id(message.from_user.id)
    d = service.draft(user.id) if user else None
    if not d:
        return
    a, step = d['answers'].copy(), d['step']
    text = (message.text or '').strip()
    if step in ('weight', 'chest', 'waist', 'hips'):
        try:
            value = float(text.replace(',', '.'))
        except ValueError:
            value = float('nan')
        valid = is_valid_weight(text) if step == 'weight' else 10 <= value <= 300
        if not valid:
            await message.answer('Вкажіть коректне число: вага 30–400 кг, заміри 10–300 см. Наприклад: 85,6.')
            return
        a[step] = round(value, 1)
        next_step = {'weight': 'confirm_weight', 'chest': 'waist', 'waist': 'hips', 'hips': 'review'}[step]
    elif step in ('symptom_other', 'reason_other'):
        if not 1 <= len(text) <= 500:
            await message.answer('Введіть короткий опис від 1 до 500 символів.')
            return
        a[step] = text
        next_step = 'dose' if step == 'symptom_other' else 'measurements'
    else:
        await message.answer('Оберіть відповідь на inline-кнопках нижче.')
        await render(message, d)
        return
    if service.save(d, next_step, a):
        await render(message, service.draft(user.id))
