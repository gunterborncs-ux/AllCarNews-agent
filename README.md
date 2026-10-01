# 🚗 Auto News Agent

ИИ-агент для автоматического мониторинга мировых СМИ об автомобилях
и публикации новостей в Telegram-канал.

**Тематика:** только автомобили — новинки, концепткары, электромобили, прототипы.

## Как это работает

1. **GitHub Actions** запускает агента 4 раза в день (5:00, 9:00, 13:00, 17:00 UTC).
2. Агент **параллельно собирает** RSS-ленты 11 мировых авто-источников.
3. **Фильтрует** нерелевантные новости по брендам и ключевым словам,
   отсекает мотоциклы, запчасти, тарифы, страховки, гоночные серии.
4. **Дедуплицирует** семантически близкие заголовки через `sentence-transformers`.
5. **Суммаризирует** через бесплатную модель OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`).
6. **Публикует** 3–5 постов с жирным заголовком и ссылкой на источник.
7. **Сохраняет** историю URL в `published.json` и коммитит обратно в репозиторий.
8. **Чистит** записи старше 30 дней автоматически.
9. **Уведомляет админа** в личку при любом сбое.

## Стоимость

- **LLM:** $0 (бесплатные модели OpenRouter)
- **Инфраструктура:** $0 (GitHub Actions, 2000 минут/мес на приватных репо)
- **Telegram Bot API:** $0
- **Внешний триггер:** $0 (cron-job.org)

## Настройка

### 1. Создайте Telegram-бота

1. Откройте [@BotFather](https://t.me/BotFather), отправьте `/newbot`.
2. Получите токен для нового бота (например, `@AutoNewsBot`).
3. Добавьте бота в автомобильный канал как **администратора**
   с правом публикации сообщений.

### 2. Получите API-ключ OpenRouter

1. Зарегистрируйтесь на [openrouter.ai](https://openrouter.ai).
2. Создайте ключ на [openrouter.ai/keys](https://openrouter.ai/keys).

### 3. Узнайте свой Telegram user ID

1. Откройте [@userinfobot](https://t.me/userinfobot), нажмите Start.
2. Скопируйте число после `Id:` — это ваш `ADMIN_CHAT_ID`.
3. **Обязательно** напишите `/start` своему боту в личке — иначе он
   не сможет отправлять вам уведомления.

### 4. Добавьте секреты в GitHub

**Settings → Secrets and variables → Actions → New repository secret**:

| Секрет | Значение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен от @BotFather |
| `TELEGRAM_CHANNEL_ID` | `@your_auto_channel` или `-100...` |
| `OPENROUTER_API_KEY` | Ключ OpenRouter |
| `ADMIN_CHAT_ID` | Ваш user ID из @userinfobot |

### 5. Включите права на запись

**Settings → Actions → General → Workflow permissions** → выберите
**Read and write permissions**. Это нужно для шага коммита `published.json`.

### 6. Запустите workflow

Перейдите во вкладку **Actions → Auto News Agent → Run workflow**.
Первый автоматический запуск произойдёт по расписанию.

## Внешний триггер (рекомендуется)

Встроенный планировщик GitHub Actions может задерживать или пропускать
запуски в часы пик. Для надёжности настройте внешний триггер через
[cron-job.org](https://cron-job.org/).

### Создание GitHub PAT

1. **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**.
2. **Generate new token (classic)**.
3. Отметьте scope **`repo`**.
4. Скопируйте токен.

### Настройка cron-job.org

**Create cronjob**:

| Поле | Значение |
|---|---|
| Title | `Trigger Auto News Agent` |
| URL | `https://api.github.com/repos/ВАШ_ЛОГИН/ИМЯ_РЕПО/actions/workflows/auto-news-agent.yml/dispatches` |
| Timezone | `Europe/Moscow (UTC+03:00)` |
| Hours | `8, 12, 16, 20` |
| Minutes | `0` |
| Request method | `POST` |

**Headers**:

| Ключ | Значение |
|---|---|
| `Accept` | `application/vnd.github+json` |
| `Authorization` | `Bearer ВАШ_ТОКЕН` |
| `Content-Type` | `application/json` |
| `X-GitHub-Api-Version` | `2022-11-28` |

**Request body**: `{"ref":"main"}`

Нажмите **Test Run** — успешный ответ с кодом **204**.

## Локальный запуск

```bash
cp .env.example .env
# Заполните .env своими ключами
pip install -r requirements.txt
python main.py
