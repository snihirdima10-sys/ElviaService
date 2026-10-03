from datetime import date
from html import escape

from app.models.order import Order
from app.models.therapy import Therapy
from app.models.user import User
from app.services.order_service import OrderPreview
from app.utils.formatter import format_weeks

START_UPDATE_WEIGHT_TEXT = (
    "⚖️<b> Час оновити вагу</b>\n\n"
    "Будь ласка, зважтеся вранці натщесерце та внесіть актуальну вагу в бот.\n\n"
    "Якщо маєте можливість, також радимо додати актуальні заміри тіла — це допоможе точніше оцінювати зміни та ваш прогрес за цей тиждень.\n\n"
    "Регулярні вимірювання допомагають нам уважно стежити за динамікою протягом терапії.\n\n"
    "<i>Дякуємо, що дбаєте про себе разом з Elvia </i>🤍"
)


def format_request_weight(user: User):
    return (
        "⚖️ <b>Оновлення ваги</b>\n\n"
        f"Ваша поточна вага — <b>{user.current_weight} кг</b>\n\n"
        "Введіть нове значення ваги одним повідомленням у кілограмах.\n"
        "Наприклад: <i>83.7</i>\n\n"
        "Для точного відстеження прогресу рекомендуємо зважуватися вранці натщесерце та, за можливості, в однакових умовах.\n\n"
        "<i>Кожне оновлення допомагає краще бачити динаміку ваших результатів</i> 🤍"
    )

def format_confirm_weight(last_weight, new_weight : float):
    return (
        "⚖️ <b>Підтвердження ваги</b>\n\n"
        "Перевірте, будь ласка, чи правильно вказані дані:\n\n"
        f"Попередня вага — <b>{last_weight} кг</b>\n"
        f"Нова вага — <b>{new_weight} кг</b>\n\n"
        f"Різниця: <b>{round(new_weight - last_weight, 1)} кг</b>\n\n"
        "<i>Якщо все правильно, підтвердьте оновлення нижче</i> 🤍"
    )

def format_success_change_weight(last_weight: float, new_weight: float):
    return (
        "✅<b>Вагу успішно оновлено!</b>\n\n"
        f"Початкова вага — <b>{last_weight} кг</b>\n"
        f"Поточна вага — <b>{new_weight} кг</b>\n"
        f"Зміна від початку: <b>{round(new_weight - last_weight,1)} кг</b>\n\n"
        "<i>Продовжуйте дотримуватися рекомендацій лікаря та регулярно оновлювати свої показники</i> 🌿"
    )

def format_therapy(active_therapy: Therapy | None, planned_therapy: Therapy | None):
    if active_therapy:
        weeks = (date.today() - active_therapy.start_date).days // 7

        active_therapy_text = (
            f"Препарат: <b>{active_therapy.dose.medication}</b>\n"
            f"Поточне дозування: <b>{active_therapy.dose.dose_value} мг</b>\n"
            f"Початок терапії: <b>{active_therapy.start_date.strftime("%d.%m.%Y")}</b>\n"
            f"Тривалість терапії: <b>{format_weeks(weeks)}</b>"
        )
    else:
        active_therapy_text = (
            "Наразі активну терапію не призначено.\n"
            "Щоб розпочати терапію або отримати нове призначення, "
            "зверніться до лікаря.\n\n")

    if planned_therapy:
        planned_therapy_text = (
            f"Препарат: <b>{planned_therapy.dose.medication}</b>\n"
            f"Дозування: <b>{planned_therapy.dose.dose_value} мг</b>\n"
            f"Початок терапії: <b>{planned_therapy.start_date.strftime("%d.%m.%Y")}</b>\n"
        )
    else:
        planned_therapy_text = "У вас немає запланованої терапій"

    wrapper = (
        "🌿 <b>Ваша терапія</b>\n\n"
        f"{active_therapy_text}"
        "<b>\n\nЗапланована терапія</b>\n\n"
        f"{planned_therapy_text}\n\n"
        f"♻️ <i>Будь-які зміни погоджуйте з лікарем</i>"
    )

    return wrapper

def format_therapy_history(user: User, active_therapy: Therapy | None, therapies_history: list[Therapy] | None) -> str:
    if active_therapy:
        weeks = (date.today() - active_therapy.start_date).days // 7
        active_therapy_text = (
            f"<b>{active_therapy.dose.medication} • {active_therapy.dose.dose_value} мг</b>\n\n"
            f"Початок: {active_therapy.start_date.strftime("%d.%m.%Y")}\n"
            f"Тривалість: {format_weeks(weeks)}\n"
            f"Актуальна вага: {user.current_weight} кг"
        )
    else:
        active_therapy_text = "У вас поки немає активниї терапій"


    if therapies_history:

        history_therapy_text = ""
        for therapy in therapies_history:

            if therapy.end_date is None or therapy.end_weight is None:
                history_therapy_text += "Дані завершеного етапу терапії неповні. Зверніться до лікаря.\n\n"
                continue
            weeks = (therapy.end_date - therapy.start_date).days // 7
            result_weight = round(therapy.start_weight - therapy.end_weight, 1)
            history_therapy_text += (
                f"<b>{therapy.dose.medication} • {therapy.dose.dose_value} мг</b>\n\n"
                f"Період: {therapy.start_date.strftime("%d.%m")}–{therapy.end_date.strftime("%d.%m.%Y")}\n"
                f"Тривалість: {format_weeks(weeks)}\n"
                f"Вага: {therapy.start_weight} → {therapy.end_weight} кг\n"
                f"Результат: <b>{result_weight} кг</b>\n"
                f"──────────────\n"
            )
    else:
        history_therapy_text = "У вас поки немає завершених терапій"


    stages = list(therapies_history or [])
    if active_therapy:
        stages.append(active_therapy)
    overall_duration = "терапію ще не розпочато"
    if stages:
        first_start = min(stage.start_date for stage in stages)
        overall_duration = format_weeks(max(0, (date.today() - first_start).days // 7))
    overall_result = (
        f"Початкова вага: {user.start_weight} кг\n"
        f"Актуальна вага: {user.current_weight} кг\n"
        f"Зміна ваги: <b>{round(user.current_weight - user.start_weight, 1)} кг</b>\n"
        f"Час від початку терапії: {overall_duration}\n\n"
        "♻️️ <i>Зміна дозування можлива лише після погодження з лікарем</i>"
    )

    wrapper = (
        "👤 <b>Історія терапії</b>\n\n"
        "Тут зберігаються всі етапи терапії, зміни дозування та динаміка ваги\n\n"
        "✅ <b>Поточний етап</b>\n\n"
        f"{active_therapy_text}\n\n"
        f"─────────────────────\n\n"
        "<b>💉 Історія дозувань</b>\n\n"
        f"{history_therapy_text}\n\n"
        "\n📊 <b>Загальний результат терапії</b>\n\n"
        f"{overall_result}"
    )
    return wrapper

def format_orders_text(orders: list[Order]) -> str:
    orders_text = "📦 <b>Історія замовлень</b>\n\n"
    status_labels = {
        "new": "Нове",
        "processed": "Оброблено",
        "completed": "Завершено",
    }

    i = 1
    for order in orders:
        orders_text += (
            f"🪴<b>Замовлення №{i}</b>\n\n"
            f"{order.dose.medication} - {order.dose.dose_value} мг\n"
            f"Курс: {format_weeks(order.weeks_count)}\n"
            f"Сума: {order.total_price:.0f} грн\n"
            f"Дата: {order.created_at.strftime('%d.%m.%Y')}\n"
            f"Статус: {status_labels.get(order.status, 'Уточнюється')}\n\n"
        )

        if i < len(orders):
            i += 1
            orders_text += "────────────────────────\n\n"

    return orders_text

def format_order_details(user: User, active_therapy: Therapy, order_preview: OrderPreview) -> str:
    text = (
        "📦 <b>Перевірте ваше замовлення</b>\n\n"
        f"💉 Препарат: <b>{active_therapy.dose.medication}</b>\n"
        f"Дозування: <b>{active_therapy.dose.dose_value} мг</b>\n"
        f"Період: <b>{format_weeks(order_preview.weeks_count)}</b>\n"
        f"До сплати: <b>{order_preview.total_price:.0f} грн</b>\n\n"
        f"👤 Одержувач: <b>{user.full_name}</b>\n"
        f"Телефон: <b>{user.phone}</b>\n\n"
        f"🚚 <b>Доставка</b>\n{escape(order_preview.delivery_data)}\n\n"
        f"Будь ласка, перевірте вказані дані перед підтвердженням замовлення."
    )
    return text

