# 🤖 AI Post Generator

**AI News Bot** — это автоматизированная система для сбора новостей из различных источников (RSS/Telegram), их фильтрации, генерации Telegram-постов с помощью ИИ и автоматической публикации в канал. 

## 🏗 Архитектура и Стек Технологий

Проект построен на микросервисной архитектуре с асинхронным конвейером обработки:
`Источники → Парсинг → Фильтрация → AI-генерация → Публикация в Telegram`.

*   **Web API:** FastAPI + Uvicorn.
*   **База данных:** PostgreSQL + SQLAlchemy (async) + Alembic.
*   **Очередь задач:** Celery + RabbitMQ (брокер) + Redis (backend).
*   **ИИ-провайдеры:** Google Gemini (основной) и OpenAI GPT-4o-mini (запасной).
*   **Интеграция с Telegram:** Telethon (для парсинга каналов и публикации).
*   **Деплой и инфраструктура:** Docker Compose.

---

## 📁 Структура проекта

## 📁 Структура проекта

*   `app/main.py` — Основная точка входа FastAPI приложения, объединяющая роутеры (`sources`, `keywords`, `news`, `posts`, `generate`, `auth`).
*   `app/api/` — REST API эндпоинты (FastAPI) для управления источниками, ключевыми словами, новостями, постами и авторизацией сессии.
*   `app/ai/` — Модуль взаимодействия с ИИ:
    *   `client.py` (`AIClient`) — Единая точка доступа к Gemini и OpenAI с обработкой ошибок и переключением провайдеров.
    *   `generator.py` (`PostGenerator`) — Формирование системных и пользовательских промптов, валидация длины и формата готового поста.
*   `app/news_parser/` — Модули сбора новостей: парсер RSS-лент (`rss.py`) и парсер сообщений из Telegram-каналов (`telegram.py`).
*   `app/repository/` — Слой доступа к данным (Data Access Layer) с использованием асинхронных репозиториев SQLAlchemy (`news_repo.py`, `post_repo.py` и др.).
*   `app/services/` — Сервисный слой с бизнес-логикой приложения, включая `filter.py` (фильтрация новостей по длине, дубликатам хэша, активности источника и ключевым словам).
*   `app/tasks/` — Асинхронные Celery-задачи:
    *   `parsing.py` — Задачи парсинга RSS и Telegram-источников.
    *   `pipeline.py` — Оркестратор отбора необработанных новостей и передачи их на генерацию.
    *   `generation.py` — Задача генерации текста поста через ИИ.
    *   `publishing.py` — Задача публикации готового поста в Telegram.
*   `app/telegram/` — Модуль интеграции с Telegram via Telethon (`client.py` для управления сессией и `publisher.py` для отправки сообщений в канал).
*   `app/config.py` — Конфигурация приложения и валидация переменных окружения (`.env`) через Pydantic Settings.
*   `app/database.py` — Настройка асинхронного подключения к PostgreSQL, создание движка и сессий SQLAlchemy.
*   `app/models.py` — ORM-модели базы данных (`Source`, `Keyword`, `NewsItem`, `Post`).
*   `app/schemas.py` — Pydantic-схемы для валидации входящих и исходящих DTO/запросов API.
*   `alembic/` — Файлы и скрипты версионирования и миграций базы данных.
*   `celery_worker.py` — Инициализация приложения Celery, регистрация задач и настройка расписания периодических запусков (Celery Beat).
*   `docker-compose.yaml` — Конфигурация оркестрации всех контейнеров (PostgreSQL, Redis, RabbitMQ, API, Celery Worker, Celery Beat, Flower).
*   `pyproject.toml` / `requirements.txt` — Конфигурация окружения, управление зависимостями и пакетами Python.

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

Все API-запросы подробно задокументированы в FastAPI (`/docs`).

Примеры 

Добавление нового RSS-источника:

`curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sources/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "TechCrunch RSS",
  "source_type": "rss",
  "url": "https://techcrunch.com/feed/",
  "enabled": true
}'`

Добавление ключевого слова для фильтра:
`
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/keywords/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "word": "python",
  "pattern": "string",
  "enabled": true
}'
`


### Ручной запуск задач
Если вы не хотите ждать срабатывания расписания (Celery Beat каждые 30 минут), вы можете запустить процесс вручную из консоли:

Спарсить все активные источники:

`docker compose exec celery_worker celery -A celery_worker call tasks.parse_all_sources`

Запустить конвейер фильтрации, генерации и публикации:
`docker compose exec celery_worker celery -A celery_worker call tasks.run_pipeline
`
💡 Мониторинг: Для визуального отслеживания состояния очередей и задач используйте панель Flower, доступную по адресу http://localhost:5555.