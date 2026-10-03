import re

def is_valid_full_name(full_name: str) -> bool:
    full_name = full_name.strip()
    parts = full_name.split()

    if len(parts) < 2 or len(parts) > 3:
        return False

    for part in parts:
        if len(part) < 2:
            return False

        if not part.replace('-','').replace("'",'').replace("’",'').isalpha():
            return False

    return True

def is_valid_height(height: str) -> bool:
    if not height.isdigit():
        return False

    height = int(height)

    return 100 <= height <= 200

def is_valid_weight(weight: str) -> bool:
    try:
        weight = float(weight.replace(",", "."))
    except ValueError:
        return False

    return 30 <= weight <= 400

def normalize_phone(phone: str) -> str | None:
    phone = re.sub(r"\D", "", phone)

    if phone.startswith("380") and len(phone) == 12:
        return f"+{phone}"

    if phone.startswith("0") and len(phone) == 10:
        return f"+38{phone}"

    if len(phone) == 9:
        return f"+380{phone}"

    return None

def is_valid_phone(phone: str) -> bool:
    return re.fullmatch(r"\+?[1-9][0-9]{6,14}", phone.strip()) is not None


def is_valid_city(text: str) -> bool:
    text = text.strip()
    return 2 <= len(text) <= 100 and any(char.isalpha() for char in text) and all(
        char.isalpha() or char.isdecimal() or char in " -'’ʼ()." for char in text
    )


def is_valid_delivery_address(text: str, method: str | None) -> bool:
    text = text.strip()
    if method in ("branch", "parcel_locker"):
        return re.fullmatch(r"[0-9]{1,10}", text) is not None and int(text) > 0
    if method == "courier_delivery":
        return 5 <= len(text) <= 300 and any(char.isalpha() for char in text) and any(
            char.isdecimal() for char in text
        )
    return False

def validate_delivery_data(text: str) -> dict | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) != 4:
        return None

    full_name, phone, city, branch = lines

    if len(full_name.split()) < 2:
        return None

    normalized_phone = normalize_phone(phone)

    if normalized_phone is None:
        return None

    if len(city) < 2:
        return None

    if len(branch) < 2:
        return None

    return {
        "full_name": full_name,
        "phone": normalized_phone,
        "city": city,
        "branch": branch
    }
