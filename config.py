import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "db.db"

load_dotenv()

# Temporary manual entry point. Automatic check-ins do not depend on this flag.
CHECKIN_TEST_BUTTON_ENABLED = os.getenv("CHECKIN_TEST_BUTTON_ENABLED", "true").lower() in {"1", "true", "yes"}

PAYMENT_RECIPIENT = os.getenv("PAYMENT_RECIPIENT", "").strip()
PAYMENT_TEST_MODE = os.getenv("PAYMENT_TEST_MODE", "false").lower() in {"1", "true", "yes"}
PAYMENT_IBAN = "".join(os.getenv("PAYMENT_IBAN", "").split()).upper()
PAYMENT_PURPOSE = os.getenv("PAYMENT_PURPOSE", "Оплата замовлення Elvia").strip() or "Оплата замовлення Elvia"

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL_GOOGLE_FORM = os.environ["URL_GOOGLE_FORM"]
DOCTOR_URL = os.environ["DOCTOR_URL"]
CHANNEL_URL = os.environ["CHANNEL_URL"]
DOCTOR_ID = [int(os.environ["DOCTOR_ID"])]
