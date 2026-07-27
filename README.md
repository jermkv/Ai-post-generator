# 🤖 AI Post Generator

**AI News Bot** — это автоматизированная система для сбора новостей из различных источников (RSS/Telegram), их фильтрации, генерации Telegram-постов с помощью ИИ и автоматической публикации в канал. 

## 🏗 Архитектура и Стек Технологий

Проект построен на микросервисной архитектуре с асинхронным конвейером обработки:
`Источники → Парсинг → Фильтрация → AI-генерация → Публикация в Telegram`.

*   **Web API:** FastAPI + Uvicorn.
*   **База данных:** PostgreSQL + SQLAlchemy (async) + Alembic.
*   **Очередь задач:** Celery + RabbitMQ (брокер) + Redis (backend).
*   **ИИ-провайдеры:** Google Gemini (основной, `gemini-2.5-flash`) и OpenAI GPT-4o-mini (запасной).
*   **Интеграция с Telegram:** Telethon (для парсинга каналов и публикации).
*   **Деплой и инфраструктура:** Docker Compose.

---

## 📁 Структура проекта

*   `app/main.py` — основной файл FastAPI приложения, объединяющий роутеры (`sources`, `keywords`, `news`, `posts`, `generate`, `auth`).
*   `app/ai/` — модуль работы с ИИ. Содержит `AIClient` (единая точка доступа) и `PostGenerator` (формирование промптов и валидация длины).
*   `app/tasks/` — Celery-задачи:
    *   `parsing.py` — задачи парсинга RSS и Telegram.
    *   `pipeline.py` — оркестратор обработки и генерации.
    *   `generation.py` — генерация постов.
    *   `publishing.py` — публикация в Telegram.
*   `app/services/filter.py` — сервис фильтрации новостей по длине, наличию дубликатов (хэш контента), статусу источника и ключевым словам.
*   `app/news_parser/` — логика парсеров (`rss.py` и `telegram.py`).
*   `app/models.py` — ORM модели базы данных (`Source`, `Keyword`, `NewsItem`, `Post`).

---

## 🚀 Инструкция по запуску

### Шаг 1. Настройка переменных окружения
Создайте файл `.env` в корневой директории проекта и заполните его вашими данными:

DATABASE_URL=postgresql+asyncpg://postgres:pass@postgres:5432/aibot
RABBIT_URL=amqp://guest:guest@rabbitmq:5672//
REDIS_URL=redis://redis:6379/0

# Настройки Telegram (получить на my.telegram.org)
TG_API_ID=ваш_api_id
TG_API_HASH=ваш_api_hash
TG_TARGET_CHANNEL=@ваш_канал

# Ключи API
OPENAI_API_KEY=ваш_openai_ключ
GEMINI_API_KEY=ваш_gemini_ключ

### Шаг 2. Запуск контейнеров
Поднимите всю инфраструктуру (PostgreSQL, Redis, RabbitMQ, API, Celery Workers, Flower) с помощью Docker:

Bash
`docker compose up --build`

### Шаг 3. Авторизация Telegram-сессии
Чтобы Telethon мог парсить закрытые каналы и публиковать посты, необходимо один раз создать файл сессии через API.

Откройте Swagger UI: http://localhost:8000/docs.

Перейдите в секцию Telegram Auth.

Выполните запрос POST /api/v1/auth/send-code, указав номер телефона.

Выполните запрос POST /api/v1/auth/sign-in, передав полученный в Telegram код.

После успешной авторизации файл session сохранится автоматически, и система будет готова к работе.

## 📡 Примеры API-запросов и Тестирование

Ручной запуск задач
Если вы не хотите ждать срабатывания расписания (Celery Beat каждые 30 минут), вы можете запустить процесс вручную из консоли:

Спарсить все активные источники:

Bash
docker compose exec celery_worker celery -A celery_worker call tasks.parse_all_sources
Запустить конвейер фильтрации, генерации и публикации:

Bash
docker compose exec celery_worker celery -A celery_worker call tasks.run_pipeline

💡 Мониторинг: Для визуального отслеживания состояния очередей и задач используйте панель Flower, доступную по адресу http://localhost:5555.