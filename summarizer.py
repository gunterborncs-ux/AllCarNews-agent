"""
Суммаризация новостей об автомобилях через OpenRouter.

Формат ответа — обычный текст с разделителем ===POST===.
Жёсткая валидация: пост отклоняется, если кириллицы в нём меньше 40%.
"""
import logging
import re

from openai import AsyncOpenAI

from config import (
    OPENROUTER_KEY,
    OPENROUTER_BASE,
    PRIMARY_MODEL,
    FALLBACK_MODEL,
)

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    base_url=OPENROUTER_BASE,
    api_key=OPENROUTER_KEY,
)

SYSTEM_PROMPT = """Ты — редактор русскоязычного Telegram-канала об автомобилях.

⚠️ ГЛАВНОЕ ПРАВИЛО: все посты ТОЛЬКО на русском языке.
Если новость на английском — ПЕРЕВЕДИ её на русский. Названия моделей
(Tesla Model 3, BMW iX, Toyota Camry) оставляй латиницей, всё остальное —
по-русски.

Создай от 3 до 5 постов ТОЛЬКО об автомобилях: новинки, концепткары,
электромобили, прототипы, утечки, даты презентаций, характеристики.

ИГНОРИРУЙ: мотоциклы, запчасти, шины, тарифы, страховки, налоги,
F1/NASCAR/MotoGP, водный и воздушный транспорт, сельхозтехнику.

Требования к каждому посту:
- Первая строка: эмодзи, пробел, затем ОБЯЗАТЕЛЬНО заголовок
  в теге <b>...</b> (до 80 символов, на русском)
- Вторая строка: пустая
- Затем 2–3 предложения НА РУССКОМ: модели, характеристики, цифры, сроки
- В конце — ссылка: <a href="URL">Источник</a>
- До 600 символов
- Эмодзи ВНЕ тега <b>, например: 🚗 <b>Заголовок</b>

ПРИМЕР ПРАВИЛЬНОГО ПОСТА:

===POST===

🚗 <b>Tesla представила обновлённый Model Y</b>

Электрокроссовер получил новую батарею на 82 кВт·ч и запас хода
до 600 км по циклу WLTP. Производство стартует в первом квартале 2027 года.
<a href="URL1">Источник</a>

ЗАПРЕЩЕНО:
- Писать посты на английском
- Использовать **markdown** вместо <b>
- Добавлять пояснения до/после постов
- URL брать не из исходных данных

Между постами — строго строка ===POST===.
"""


def _clean_unicode(text: str) -> str:
    if not text:
        return text
    try:
        text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
    except (UnicodeDecodeError, UnicodeEncodeError):
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    text = re.sub(r"[\u200b-\u200f\ufeff\u2028\u2029]", "", text)
    text = re.sub(r"[\u00a0\u2000-\u200a\u202f\u205f\u3000]", " ", text)
    return text


def _clean_post(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[\w]*\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1F300 <= cp <= 0x1FAFF
        or 0x1F000 <= cp <= 0x1F2FF
        or 0x2600 <= cp <= 0x27BF
        or 0x2B00 <= cp <= 0x2BFF
    )


def _cyrillic_ratio(text: str) -> float:
    """
    Доля кириллических букв среди всех букв (латиница + кириллица).
    Если букв нет вообще — вернуть 0.
    """
    cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    total = cyrillic + latin
    if total == 0:
        return 0.0
    return cyrillic / total


def _is_valid_post(text: str, max_len: int = 600) -> bool:
    """
    Пост должен:
    - начинаться с эмодзи
    - содержать <a href=
    - содержать <b>...</b>
    - иметь >= 40% кириллицы (иначе считаем «англоязычным»)
    - быть не длиннее max_len
    """
    if not text or len(text) > max_len:
        return False
    stripped = text.strip()
    if not stripped or not _is_emoji(stripped[0]):
        return False
    if "<a href=" not in stripped:
        return False
    if "<b>" not in stripped:
        return False

    ratio = _cyrillic_ratio(stripped)
    if ratio < 0.40:
        logger.warning(
            "Пост отклонён: кириллицы %.0f%% (<40%%). Начало: %r",
            ratio * 100, stripped[:100],
        )
        return False
    return True


_DELIMITER = re.compile(r"===+\s*POST\s*===+", re.IGNORECASE)


def _parse_posts(raw: str) -> list[str]:
    if not raw or len(raw) < 50:
        logger.warning("Ответ модели слишком короткий (%d символов)", len(raw))
        return []

    raw = _clean_unicode(raw)

    if _DELIMITER.search(raw):
        parts = _DELIMITER.split(raw)
        logger.info("Разделитель ===POST=== сработал, частей: %d", len(parts))
    else:
        logger.warning("Разделитель ===POST=== не найден")
        return []

    posts: list[str] = []
    for i, part in enumerate(parts):
        cleaned = _clean_post(part)
        if _is_valid_post(cleaned):
            posts.append(cleaned)
        elif cleaned:
            logger.warning(
                "Пост #%d отклонён (len=%d, кириллица=%.0f%%): %r",
                i, len(cleaned), _cyrillic_ratio(cleaned) * 100,
                cleaned[:100],
            )
    return posts


async def summarize_news(articles: list[dict]) -> list[str]:
    """Превращает новости в готовые посты через OpenRouter."""
    if not articles:
        return []

    news_text = "\n\n".join(
        f"Заголовок: {a['title']}\n"
        f"Описание: {a.get('summary', '')[:250]}\n"
        f"Ссылка: {a['link']}"
        for a in articles[:30]
    )

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            logger.info("Запрос к модели: %s", model)
            response = await _client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": news_text},
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            choice = response.choices[0]
            finish = getattr(choice, "finish_reason", "unknown")
            raw = choice.message.content or ""
            logger.info(
                "Сырой ответ (%d символов, finish=%s)", len(raw), finish,
            )

            posts = _parse_posts(raw)
            if posts:
                logger.info("Модель %s: валидных постов %d", model, len(posts))
                return posts

            logger.warning("Модель %s: ни один пост не прошёл валидацию", model)

        except Exception as exc:
            logger.error("Ошибка модели %s: %s", model, exc, exc_info=True)

    logger.error("Все модели недоступны или вернули невалидные посты")
    return []
