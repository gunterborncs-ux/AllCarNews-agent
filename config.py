# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
# Токен для НОВОГО бота, созданного для автомобильного канала
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# ID или @username вашего НОВОГО автомобильного канала
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@allcarnewshub")

# --- OpenRouter ---
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

PRIMARY_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
FALLBACK_MODEL = "cohere/north-mini-code:free"

# --- Агент ---
MAX_ARTICLES_PER_RUN = 30
MAX_POSTS_PER_RUN = 5
SIMILARITY_THRESHOLD = 0.82
HISTORY_FILE = "published.json"
POST_DELAY_SECONDS = 3
HISTORY_RETENTION_DAYS = 30

# --- Уведомления об ошибках ---
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0") or 0)
