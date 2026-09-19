import re

def validate_full_name(full_name: str) -> bool:
    full_name = full_name.strip()
    parts = full_name.split()

    if len(parts) < 2 or len(parts) > 3:
        return False

    for part in parts:
        if len(part) < 2:
            return False

        if not part.replace('-','').replace("'",'').isalpha():
            return False

    return True

def validate_height(height: str) -> bool:
    if not height.isdigit():
        return False

    height = int(height)

    return 100 <= height <= 200

def validate_weight(weight: str) -> bool:
    try:
        weight = float(weight.replace(",", "."))
    except ValueError:
        return False

    return 30 <= weight <= 400

def validate_phone(phone: str) -> bool:
    phone = phone.strip()

    # прибираємо пробіли, дужки та дефіси
    phone = re.sub(r"[()\s-]", "", phone)

    # міжнародний формат: + і від 10 до 15 цифр
    pattern = r"^\+\d{10,15}$"

    return bool(re.fullmatch(pattern, phone))