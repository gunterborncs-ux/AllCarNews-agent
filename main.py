"""
Auto News Agent.

Медиа (фото + видео) берётся ТОЛЬКО из HTML статьи.
RSS — только источник заголовков и ссылок.
Ссылка в посте — <a href="URL">Источник</a>.
Фото дедуплицируются по нормализованному URL.
"""
import asyncio
import json
import logging
import re
import traceback
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

import aiohttp
import feedparser
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from bs4 import BeautifulSoup

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
    ADMIN_CHAT_ID,
    MAX_ARTICLES_PER_RUN,
    MAX_POSTS_PER_RUN,
    SIMILARITY_THRESHOLD,
    HISTORY_FILE,
    POST_DELAY_SECONDS,
    HISTORY_RETENTION_DAYS,
)
from dedup import deduplicate
from rss_sources import RSS_FEEDS, CAR_BRANDS, AUTO_KEYWORDS, STOP_WORDS
from storage import (
    load_history,
    save_history,
    filter_unpublished,
    cleanup_old,
    add_urls,
)
from summarizer import summarize_news

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent")

_LEAK_MARKERS = (
    "thinking process", "chain of thought", "analyze user input",
    "here's a", "let me think", "мысленный процесс", "размышляю",
)

_HREF_RE = re.compile(r'<a\s+href="([^"]+)"', re.IGNORECASE)
_MAX_PHOTOS_PER_POST = 10

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_JUNK_MARKERS = (
    "/pixel", "1x1", "spacer", "tracking", "beacon",
    "favicon", "/icon/", "avatar", "logo.svg", "/emoji/",
)

# Регулярки для YouTube / Vimeo embed
_YT_RE = re.compile(
    r"(?:youtube\.com/(?:embed|watch\?v=)|youtu\.be/)([A-Za-z0-9_\-]{6,})",
    re.IGNORECASE,
)
_VIMEO_RE = re.compile(r"vimeo\.com/(?:video/)?(\d+)", re.IGNORECASE)


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- Нормализация URL картинок ----------

_SIZE_QUERY_KEYS = {
    "w", "h", "width", "height", "q", "quality",
    "resize", "fit", "crop", "auto", "dpr", "scale",
    "size", "v", "ver", "version",
}

_SIZE_SUFFIX_RE = re.compile(
    r"""
    (?:[-_@](?:
        \d+x\d+
        |\d+w
        |\d+h
        |\d{2,4}
        |thumb|thumbnail
        |small|medium|large|big|mini
        |preview|scaled|resized
        |2x|3x
    ))+
    (?=\.(?:jpe?g|png|webp|gif|avif)$)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize_image_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
    except Exception:
        return url.lower()

    qs = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {
        k: v for k, v in qs.items()
        if k.lower() not in _SIZE_QUERY_KEYS
    }
    new_query = "&".join(
        f"{k}={v[0]}" for k, v in sorted(filtered.items())
    )
    path = _SIZE_SUFFIX_RE.sub("", parsed.path).lower()

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        new_query,
        "",
    ))


# ---------- Фото и видео из HTML статьи ----------

def _extract_video_url_from_embed(embed_url: str) -> str | None:
    """
    Из embed-ссылки YouTube/Vimeo возвращает прямой URL страницы видео.
    Telegram не умеет проигрывать embed, но умеет плеер по обычной ссылке.
    """
    m = _YT_RE.search(embed_url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    m = _VIMEO_RE.search(embed_url)
    if m:
        return f"https://vimeo.com/{m.group(1)}"
    return None


async def fetch_article_media(
    session: aiohttp.ClientSession, url: str,
) -> tuple[list[str], str | None]:
    """
    Загружает HTML статьи и возвращает (images, video_url).

    Фото:
      og:image, twitter:image, JSON-LD image, <img> из <article>/<main>.

    Видео (первое найденное по приоритету):
      1. og:video / og:video:url / og:video:secure_url
      2. twitter:player:stream
      3. JSON-LD video (contentUrl / embedUrl / url)
      4. <video src> или <source src> внутри <video>
      5. <iframe> с YouTube/Vimeo embed → конвертируется в обычный URL
    """
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={
                "User-Agent": _UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru,en;q=0.5",
            },
        ) as resp:
            if resp.status != 200:
                logger.warning("HTML %s → статус %s", url, resp.status)
                return [], None
            html = await resp.text(errors="ignore")
    except Exception as exc:
        logger.warning("Не удалось загрузить статью %s: %s", url, exc)
        return [], None

    soup = BeautifulSoup(html, "html.parser")
    images: list[str] = []
    seen_norm: set[str] = set()
    video: str | None = None

    def _add_img(raw: str) -> None:
        if not raw or not isinstance(raw, str):
            return
        raw = raw.strip()
        if not raw:
            return
        abs_url = urljoin(url, raw)
        low = abs_url.lower()
        if low.startswith(("data:", "blob:", "javascript:")):
            return
        if any(marker in low for marker in _JUNK_MARKERS):
            return
        if low.endswith(".svg") or ".svg?" in low:
            return

        norm = _normalize_image_url(abs_url)
        if norm and norm not in seen_norm:
            seen_norm.add(norm)
            images.append(abs_url)

    def _set_video(raw: str | None) -> None:
        nonlocal video
        if video or not raw or not isinstance(raw, str):
            return
        raw = raw.strip()
        if not raw:
            return
        abs_url = urljoin(url, raw)
        if abs_url.lower().startswith(("data:", "blob:", "javascript:")):
            return
        video = abs_url

    # ---- Фото ----

    # og:image / twitter:image
    for tag in soup.find_all("meta"):
        prop = (tag.get("property") or tag.get("name") or "").lower()
        if prop in (
            "og:image", "og:image:url", "og:image:secure_url",
            "twitter:image", "twitter:image:src",
        ):
            _add_img(tag.get("content", ""))

    # JSON-LD (image + video)
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue

            img = item.get("image")
            if isinstance(img, str):
                _add_img(img)
            elif isinstance(img, list):
                for x in img:
                    if isinstance(x, str):
                        _add_img(x)
                    elif isinstance(x, dict):
                        _add_img(x.get("url", ""))
            elif isinstance(img, dict):
                _add_img(img.get("url", ""))

            vid = item.get("video")
            if isinstance(vid, dict):
                for key in ("contentUrl", "embedUrl", "url"):
                    if vid.get(key):
                        _set_video(vid[key])
                        break
            elif isinstance(vid, list):
                for v in vid:
                    if isinstance(v, dict):
                        for key in ("contentUrl", "embedUrl", "url"):
                            if v.get(key):
                                _set_video(v[key])
                                break

    # <img> из основного контента
    containers = soup.find_all("article") or soup.find_all("main") or [soup]
    for container in containers:
        for img in container.find_all("img"):
            w, h = img.get("width"), img.get("height")
            try:
                if w and int(w) < 200:
                    continue
                if h and int(h) < 200:
                    continue
            except (ValueError, TypeError):
                pass
            src = (
                img.get("src")
                or img.get("data-src")
                or img.get("data-original")
                or img.get("data-lazy-src")
            )
            if not src:
                srcset = img.get("srcset") or img.get("data-srcset") or ""
                if srcset:
                    candidates = [
                        part.strip().split(" ")
                        for part in srcset.split(",")
                        if part.strip()
                    ]
                    if candidates:
                        src = candidates[-1][0]
            _add_img(src)

    # ---- Видео (если ещё не нашли) ----

    if not video:
        # og:video / twitter:player:stream
        for tag in soup.find_all("meta"):
            prop = (tag.get("property") or tag.get("name") or "").lower()
            if prop in (
                "og:video", "og:video:url", "og:video:secure_url",
                "twitter:player:stream",
            ):
                _set_video(tag.get("content", ""))
                if video:
                    break

    if not video:
        # <video src> и <source> внутри <video>
        for video_tag in soup.find_all("video"):
            src = video_tag.get("src")
            if src:
                _set_video(src)
                if video:
                    break
            for source in video_tag.find_all("source"):
                src = source.get("src")
                if src:
                    _set_video(src)
                    if video:
                        break
            if video:
                break

    if not video:
        # YouTube / Vimeo embed
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src") or iframe.get("data-src") or ""
            if not src:
                continue
            direct = _extract_video_url_from_embed(src)
            if direct:
                _set_video(direct)
                if video:
                    break

    return images[:_MAX_PHOTOS_PER_POST], video


# ---------- RSS (только заголовки и ссылки) ----------

async def fetch_rss(session: aiohttp.ClientSession, url: str) -> list[dict]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            raw = await resp.read()
        feed = feedparser.parse(raw)
        articles: list[dict] = []
        for entry in feed.entries[:15]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            articles.append({
                "title": title,
                "link": link,
                "summary": (entry.get("summary") or "").strip(),
            })
        return articles
    except Exception as exc:
        logger.warning("RSS %s: %s", url, exc)
        return []


def is_relevant(article: dict) -> bool:
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    if any(stop in text for stop in STOP_WORDS):
        return False
    if any(brand in text for brand in CAR_BRANDS):
        return True
    if any(kw in text for kw in AUTO_KEYWORDS):
        return True
    return False


async def collect_all_news() -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rss(session, url) for url in RSS_FEEDS]
        results = await asyncio.gather(*tasks)

    all_articles = [a for feed in results for a in feed]
    relevant = [a for a in all_articles if is_relevant(a)]
    logger.info("Собрано статей: %d, релевантных: %d", len(all_articles), len(relevant))
    return relevant


# ---------- Матчинг пост → статья ----------

def _match_article(post: str, articles: list[dict]) -> dict | None:
    hrefs = set(_HREF_RE.findall(post))
    if not hrefs:
        return None
    for article in articles:
        if article.get("link") in hrefs:
            return article
    for article in articles:
        norm = (article.get("link") or "").rstrip("/")
        if not norm:
            continue
        for url in hrefs:
            if url.rstrip("/") == norm:
                return article
    return None


# ---------- Уведомления ----------

async def notify_admin(bot: Bot, reason: str, details: str = "") -> None:
    if not ADMIN_CHAT_ID:
        return
    text = f"⚠️ <b>Auto News Agent</b>\n\n{reason}"
    if details:
        text += f"\n\n<code>{_html_escape(details[:800])}</code>"
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=text,
            parse_mode="HTML", disable_web_page_preview=True,
        )
        logger.info("Уведомление отправлено админу")
    except Exception as exc:
        logger.error("Не удалось отправить уведомление: %s", exc)


# ---------- Публикация ----------

async def _send_single_post(
    bot: Bot, post: str, images: list[str], video: str | None,
) -> bool:
    """
    Приоритет:
      1. Видео (sendVideo) — фото игнорируются (ограничение Telegram).
      2. Альбом 2+ фото (sendMediaGroup).
      3. Одно фото (sendPhoto).
      4. Текст (sendMessage).
    """
    if video:
        try:
            await bot.send_video(
                chat_id=CHANNEL_ID,
                video=video,
                caption=post,
                parse_mode="HTML",
            )
            logger.info("Пост с видео: %s...", post[:60])
            return True
        except Exception as exc:
            logger.warning("Видео не отправилось, fallback: %s", exc)

    photos = images[:_MAX_PHOTOS_PER_POST]
    if len(photos) >= 2:
        try:
            media = [
                InputMediaPhoto(
                    media=url,
                    caption=post if i == 0 else None,
                    parse_mode="HTML" if i == 0 else None,
                )
                for i, url in enumerate(photos)
            ]
            await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            logger.info("Пост-альбом (%d фото): %s...", len(photos), post[:60])
            return True
        except Exception as exc:
            logger.warning("Альбом не отправился, fallback: %s", exc)

    if photos:
        try:
            await bot.send_photo(
                chat_id=CHANNEL_ID, photo=photos[0], caption=post, parse_mode="HTML",
            )
            logger.info("Пост с фото: %s...", post[:60])
            return True
        except Exception as exc:
            logger.warning("Фото не отправилось, fallback: %s", exc)

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID, text=post,
            parse_mode="HTML", disable_web_page_preview=True,
        )
        logger.info("Текстовый пост: %s...", post[:60])
        return True
    except Exception as exc:
        logger.error("Ошибка публикации: %s", exc)
        return False


async def publish_posts(
    bot: Bot, posts: list[str], articles: list[dict],
) -> list[str]:
    """
    Для каждого поста всегда загружает HTML статьи и берёт фото и видео
    оттуда. RSS медиа не используется вообще.
    """
    published: list[str] = []
    async with aiohttp.ClientSession() as session:
        for post in posts:
            article = _match_article(post, articles)
            images: list[str] = []
            video: str | None = None

            if article:
                logger.info("Загружаю HTML статьи %s", article["link"])
                images, video = await fetch_article_media(
                    session, article["link"],
                )
                logger.info(
                    "Из HTML: фото=%d, видео=%s",
                    len(images), "да" if video else "нет",
                )
            else:
                logger.warning(
                    "Не удалось сопоставить пост со статьёй — публикую без медиа",
                )

            if await _send_single_post(bot, post, images, video):
                published.append(post)
                await asyncio.sleep(POST_DELAY_SECONDS)
    return published


def extract_urls(posts: list[str]) -> set[str]:
    urls: set[str] = set()
    for post in posts:
        for m in _HREF_RE.findall(post):
            urls.add(m)
    return urls


# ---------- Основной цикл ----------

async def run_cycle() -> None:
    logger.info("=== Старт цикла ===")
    bot = Bot(token=BOT_TOKEN)
    try:
        articles = await collect_all_news()
        if not articles:
            logger.warning("Нет релевантных статей")
            await notify_admin(bot, "🚨 <b>Не собрано ни одной релевантной статьи</b>")
            return

        articles = articles[:MAX_ARTICLES_PER_RUN]
        history = load_history(HISTORY_FILE)
        articles = filter_unpublished(articles, history)
        logger.info("После фильтра по истории: %d", len(articles))

        if not articles:
            logger.info("Все статьи уже опубликованы")
            return

        articles = deduplicate(articles, threshold=SIMILARITY_THRESHOLD)
        logger.info("После дедупликации: %d", len(articles))
        if not articles:
            return

        posts = await summarize_news(articles)
        logger.info("Сгенерировано постов: %d", len(posts))

        clean_posts = [
            p for p in posts
            if not any(marker in p.lower() for marker in _LEAK_MARKERS)
        ]
        posts = clean_posts[:MAX_POSTS_PER_RUN]

        if not posts:
            logger.error("Нет валидных постов")
            await notify_admin(
                bot,
                "🚨 <b>LLM не сгенерировала валидных постов</b>",
                f"Статей на входе: {len(articles)}",
            )
            return

        published = await publish_posts(bot, posts, articles)
        if not published:
            await notify_admin(bot, "🚨 <b>Ни один пост не опубликован</b>")
            return

        new_urls = extract_urls(published)
        add_urls(history, new_urls)
        history = cleanup_old(history, days=HISTORY_RETENTION_DAYS)
        save_history(HISTORY_FILE, history)

        logger.info("=== Цикл завершён: опубликовано %d постов ===", len(published))

    except Exception as exc:
        tb = traceback.format_exc()
        logger.error("Необработанное исключение: %s", exc, exc_info=True)
        await notify_admin(bot, "🚨 <b>Необработанное исключение</b>", tb)
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(run_cycle())


if __name__ == "__main__":
    main()
