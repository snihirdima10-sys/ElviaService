import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "db.db"

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
URL_GOOGLE_FORM = os.environ["URL_GOOGLE_FORM"]
DOCTOR_URL = os.environ["DOCTOR_URL"]
CHANNEL_URL = os.environ["CHANNEL_URL"]