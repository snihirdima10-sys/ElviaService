from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP


def format_date(value: str | date) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime('%d.%m.%Y')


def format_money(value) -> str:
    amount = Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f'{amount:,.0f}'.replace(',', ' ')


def format_weeks(weeks: int) -> str:
    if weeks == 0:
        return "менше тижня"
    if weeks % 10 == 1 and weeks % 100 != 11:
        word = "тиждень"
    elif weeks % 10 in [2, 3, 4] and weeks % 100 not in [12, 13, 14]:
        word = "тижні"
    else:
        word = "тижнів"

    return f"{weeks} {word}"
