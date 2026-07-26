from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    database_url: str = Field(..., description='postgresql+asyncpg://user:pass@host/db')
    rabbit_url: str = Field(default='amqp://guest:guest@rabbitmq:5672//', description='URL брокера RabbitMQ')
    redis_url: str = Field(default='redis://redis:6379/0', description='Redis для хранения результатов Celery')

    #tg
    tg_api_id: int = Field(..., description='App api_id telegram')
    tg_api_hash: str = Field(..., description='App api_hash telegram')
    tg_session_name: str = Field(default='aibot', description='Имя файла сессии')
    tg_target_channel: str = Field(..., description='Куда публиковать посты')

    #openai
    openai_api_key: str = Field(..., description='API key OpenAI')
    openai_model: str = Field(default='gpt-4o-mini', description='gpt-4o-mini дешевле gpt-4')
    openai_max_tokens: int = Field(
        default=300,
        description='Максим испол токенов'
    )

    #gemini
    gemini_api_key: str = Field(...,description="API key Gemini")
    gemini_model: str = Field(default='gemini-3.5-flash', description='gemini-3.5-flash')
    gemini_max_tokens: int = Field(
        default=500,
        description='Максим испол токенов'
    )

    #parse
    parse_interval_minutes: int = Field(
        default=30,
        description='Как часто запускать парсинг'
    )
    max_news_per_source: int = Field(
        default=10,
        description='Максимум новостей за один запуск парсера'
    )

    #generate
    generate_interval_minutes: int = Field(
        default=30,
        description='Как часто запускать генерацию'
    )
    max_generate_per_source: int = Field(
        default=10,
        description='Максимум постов для генерации за один запуск таски'
    )

    #App
    app_env: str = Field(default='development', description='development / production / testing')
    log_level: str = Field(default='INFO')

    @field_validator('app_env')
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {'development', 'production', 'testing'}
        if v not in allowed:
            raise ValueError(f'app_env должен быть из {allowed}')
        return v

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
