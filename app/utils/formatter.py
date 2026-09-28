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