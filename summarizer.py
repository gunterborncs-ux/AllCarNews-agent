"""
Суммаризация новостей об автомобилях через OpenRouter.

Формат: заголовок <b>, текст, ссылка в виде <a href="URL">Источник</a>.
Жёсткая языковая валидация: кириллицы >= 40%.
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

SYSTEM_PROMPT = """You are the editor of a Russian-language Telegram channel about cars.

═══════════════════════════════════════════════════════════
🔴 CRITICAL LANGUAGE RULE — READ BEFORE ANYTHING ELSE 🔴
═══════════════════════════════════════════════════════════
OUTPUT LANGUAGE: RUSSIAN ONLY.

- Even if the input news is in English (or any other language),
  you MUST translate it and write the post in RUSSIAN.
- Do NOT output English sentences. Do NOT mix languages.
- Brand names and model names (Tesla Model 3, BMW iX, Toyota Camry,
  Porsche 911, Lucid Air) MAY stay in Latin script.
- Everything else MUST be in Russian Cyrillic.

A post written in English will be automatically REJECTED.

═══════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════
From the news list below, produce 3 to 5 separate Telegram posts.

TOPIC — CARS ONLY:
- New car models, launches, announcements
- Concept cars and prototypes
- Electric vehicles and hybrids
- Leaks, spy shots, renders of upcoming cars
- Reviews, comparisons, test drives
- Specs: engine, power, torque, range, battery, price

IGNORE (do not create posts for):
- Motorcycles, scooters, ATVs
- Parts, tires, accessories
- Tariffs, insurance, taxes, traffic laws
- F1, NASCAR, MotoGP racing series
- Water and air transport
- Agricultural machinery
- Smartphones or consumer electronics

If fewer than 3 items match the topic, produce as many as you can.
NEVER pad the list with off-topic news.

═══════════════════════════════════════════════════════════
FORMAT REQUIREMENTS (per post, all fields in RUSSIAN)
═══════════════════════════════════════════════════════════
1. First line: one emoji + space + bold headline wrapped in <b>...</b>
   - Headline: RUSSIAN, max 80 characters
   - Emoji stays OUTSIDE the <b> tag
2. Second line: empty line
3. Then 2–3 sentences IN RUSSIAN with facts, numbers, model names
4. Last line: clickable link with the label "Источник"
   - Exact format: <a href="URL">Источник</a>
   - The label MUST be the Russian word "Источник"
   - Do NOT use bare URLs
   - Do NOT use other labels ("Source", "Ссылка", "Читать")
5. Total post length: up to 600 characters
6. Tone: neutral, informative, no clickbait

═══════════════════════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════════════════════
Posts are separated by the exact line: ===POST===
Do NOT output JSON, markdown, numbering, or explanations.

═══════════════════════════════════════════════════════════
✅ CORRECT EXAMPLE (study the language and format)
═══════════════════════════════════════════════════════════

===POST===

🚗 <b>Tesla представила обновлённый Model Y</b>

Электрокроссовер получил новую батарею на 82 кВт·ч и запас хода до 600 км по циклу WLTP. Производство стартует в первом квартале 2027 года.

<a href="https://example.com/article-1">Источник</a>

===POST===

⚡ <b>Porsche показал концепт электрического Cayenne</b>

Прототип оснащён двумя электромоторами суммарной мощностью 800 л.с. и поддерживает зарядку 350 кВт. Серийная версия ожидается к концу 2027 года.

<a href="https://example.com/article-2">Источник</a>

═══════════════════════════════════════════════════════════
❌ FORBIDDEN
═══════════════════════════════════════════════════════════
- Writing posts in English (or any language other than Russian)
- Using **markdown bold** instead of <b>...</b>
- Bare URLs without <a href="...">Источник</a> wrapper
- Using any label other than "Источник" for the link
- Mixing English and Russian in body text
- Adding comments before, between, or after posts
- Inventing URLs — use ONLY URLs from the input data

Remember: OUTPUT MUST BE IN RUSSIAN, and the link MUST be
<a href="URL">Источник</a>.
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


def _normalize_source_link(text: str) -> str:
    """Приводит ссылку в конце поста к <a href="URL">Источник</a>."""
    # 1) Нормализуем существующий <a href="...">label</a>
    text = re.sub(
        r'<a\s+href="([^"]+)"[^>]*>[^<]*</a>',
        r'<a href="\1">Источник</a>',
        text,
        flags=re.IGNORECASE,
    )

    # 2) Если <a href> нет, оборачиваем последний голый URL
    if "<a href=" not in text.lower():
        matches = list(re.finditer(r'https?://[^\s<>"\']+', text))
        if matches:
            last = matches[-1]
            url = last.group(0).rstrip(".,;:)")
            before = text[:last.start()]
            after = text[last.end():]
            text = before + f'<a href="{url}">Источник</a>' + after

    return text


def _clean_post(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[\w]*\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?i)(источник|source)\s*:\s*(https?://)", r"\2", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = _normalize_source_link(text)
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
    cyr = len(re.findall(r"[А-Яа-яЁё]", text))
    lat = len(re.findall(r"[A-Za-z]", text))
    total = cyr + lat
    return cyr / total if total else 0.0


def _is_valid_post(text: str, max_len: int = 600) -> bool:
    if not text or len(text) > max_len:
        return False
    stripped = text.strip()
    if not stripped or not _is_emoji(stripped[0]):
        return False
    if "<b>" not in stripped:
        return False
    if '<a href=' not in stripped.lower():
        return False
    if "Источник" not in stripped:
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

    if not _DELIMITER.search(raw):
        logger.warning("Разделитель ===POST=== не найден")
        return []

    parts = _DELIMITER.split(raw)
    logger.info("Разделитель сработал, частей: %d", len(parts))

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
            logger.info("Сырой ответ (%d символов, finish=%s)", len(raw), finish)

            posts = _parse_posts(raw)
            if posts:
                logger.info("Модель %s: валидных постов %d", model, len(posts))
                return posts

            logger.warning("Модель %s: ни один пост не прошёл валидацию", model)

        except Exception as exc:
            logger.error("Ошибка модели %s: %s", model, exc, exc_info=True)

    logger.error("Все модели недоступны или вернули невалидные посты")
    return []
