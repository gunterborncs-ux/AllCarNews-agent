"""
Конфигурация агента для канала об автомобилях.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@allcarnewshub")

# --- OpenRouter ---
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODELS_CHAIN = [
    "cohere/north-mini-code:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "minimax/minimax-m2-her:free",
    "openrouter/free",
]

# --- Агент ---
MAX_ARTICLES_PER_RUN = 30
MAX_POSTS_PER_RUN = 5
SIMILARITY_THRESHOLD = 0.82
HISTORY_FILE = "published.json"
POST_DELAY_SECONDS = 3
HISTORY_RETENTION_DAYS = 30

# --- Медиа ---
# Порядок: HTML (og:image) → RSS (media:content/enclosure/img) → placeholder
USE_RSS_MEDIA_FALLBACK = True
# Если ничего не нашли — генерируем placeholder, чтобы пост был с картинкой.
# False = посты без фото, если источник не отдал.
USE_PLACEHOLDER_IF_NO_PHOTO = True

# Шаблон placeholder: {text} заменится на бренд или первые слова из заголовка.
# placehold.co бесплатный, работает из любой точки, без ключа.
PLACEHOLDER_IMAGE_TEMPLATE = (
    "https://placehold.co/1200x630/1e293b/ffffff/png?text={text}"
)

# --- Уведомления об ошибках ---
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0") or 0)
