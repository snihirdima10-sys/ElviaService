from datetime import datetime, date

from app.utils.formatter import format_weeks


def format_user_card(user: dict, active_therapy: dict, planned_therapy: dict) -> str:
    weight_result = round(user["current_weight"] - user["start_weight"],1)

    patient_card = (
        "👤 <b>КАРТА ПАЦІЄНТА</b>\n\n"
        f"<b>{user["full_name"]}</b>\n\n"
        f"📱 Телефон: {user["phone"]}\n"
        f"📅 Реєстрація: {user["created_at"]}\n\n"
        "<b>Показники</b>\n\n"
        f"Зріст: <b>{user["height"]} см</b>\n"
        f"Початкова вага: <b>{user["start_weight"]} кг</b>\n"
        f"Актуальна вага: <b>{user["current_weight"]} кг</b>\n"
        f"Результат: <b>{weight_result} кг</b>\n\n"
        "━━━━━━━━━━━━━━\n\n"
    )

    if not active_therapy:
        patient_card += (
            f"💉 <b>ПОТОЧНА ТЕРАПІЯ</b>\n\n"
            f"Активних терапій немає\n\n"
            "━━━━━━━━━━━━━━\n\n"
        )
    else:
        patient_card += (
            f"💉 <b>ПОТОЧНА ТЕРАПІЯ</b>\n\n"
            f"<b>{active_therapy["medication"]} · {active_therapy['dose_value']} мг</b>\n\n"
            f"Початок терапії: <b>{active_therapy['start_date']}</b>\n\n"
            "━━━━━━━━━━━━━━\n\n"
        )

    if not planned_therapy:
        patient_card += (
            f"🌿 <b>НАСТУПНИЙ ЕТАП</b>\n\n"
            f"Запланованих терапій немає\n\n"
            "━━━━━━━━━━━━━━\n\n"
        )
    else:
        patient_card += (
            f"🌿 <b>НАСТУПНИЙ ЕТАП</b>\n\n"
            f"<b>{planned_therapy["medication"]} · {planned_therapy['dose_value']} мг</b>\n\n"
            f"Початок терапії: <b>{planned_therapy['start_date']}</b>\n"
        )

    return patient_card


def format_therapies_history(user : dict, active_therapy: dict, therapies_history: list) -> str:

    if not active_therapy:
        active_therapy_text = (
            "✅ <b>Поточний етап</b>\n\n"
            "Відсутнє активне призначення\n\n"
            f"──────────────\n\n"


        )
    else:
        start_date = datetime.strptime(active_therapy["start_date"], "%Y-%m-%d").date()
        weeks = (date.today() - start_date).days // 7

        active_therapy_text = (
            "✅ <b>Поточний етап</b>\n\n"
            f"<b>{active_therapy["medication"]} • {active_therapy["dose_value"]} мг</b>\n\n"
            f"Початок: {start_date.strftime("%d.%m.%Y")}\n"
            f"Тривалість: {format_weeks(weeks)}\n"
            f"Актуальна вага: {user["current_weight"]} кг\n\n"
            f"──────────────\n\n"


        )

    history_therapy_text = f"🌿 <b>Завершені етапи</b>\n\n"

    if therapies_history:
        for therapy in therapies_history:
            start_date = datetime.strptime(therapy["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(therapy["end_date"], "%Y-%m-%d").date()
            weeks = (date.today() - start_date).days // 7
            start_weight = therapy["start_weight"]
            end_weight = therapy["end_weight"]
            result_weight = round(start_weight - end_weight, 1)

            history_therapy_text += (
                f"<b>{therapy["medication"]} • {therapy["dose_value"]} мг</b>\n\n"
                f"Період: {start_date.strftime("%d.%m")}–{end_date.strftime("%d.%m.%Y")}\n"
                f"Тривалість: {format_weeks(weeks)}\n"
                f"Вага: {therapy["start_weight"]} → {therapy["end_weight"]} кг\n"
                f"Результат: <b>{result_weight} кг</b>\n"
                f"──────────────\n"
            )
    else:
        history_therapy_text += "Відсутні завершені терапії"

    start_date = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S").date()
    start_weight = user["start_weight"]
    current_weight = user["current_weight"]
    result_weight = round(current_weight - start_weight, 1)
    weeks = (date.today() - start_date).days // 7

    overall_result = (
        "\n📊 <b>Загальний результат терапії</b>\n\n"
        f"Початкова вага: {start_weight} кг\n"
        f"Актуальна вага: {current_weight} кг\n"
        f"Зміна ваги: <b>{result_weight} кг</b>\n"
        f"Тривалість терапії: {format_weeks(weeks)}\n\n"
        "♻️️ <i>Зміна дозування можлива лише після погодження з лікарем</i>"
    )

    return (("👤 <b>Історія терапії</b>\n\n"
            "Тут зберігаються всі етапи терапії, зміни дозування та динаміка ваги\n\n")
            + active_therapy_text + history_therapy_text + overall_result)