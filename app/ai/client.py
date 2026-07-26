import logging

from openai import (
    AsyncOpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    APIStatusError
)
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Ты - редактор русскоязычного Telegram-канала об IT и технологиях
Преобразуй переданную мысль в самостоятельный короткий пост

Правила:
1. Пиши только на русском языке.
2. Используй факты из входного текста; ничего не придумывай
3. Объекм - 2-4 коротких предложения, не более 600 символов
4. Начни с 1-2 уместных emoji
5. Сохрани важные названия продуктов, компания и технологий
6. Не используй Markdown,HTML разметку
7. В конце добавь короткий вопрос читателю, если он нужен
8. Варни только готовый текст поста
""".strip()

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    timeout=30.0,
    max_retries=2
)

class GenerationError(RuntimeError):
    """Временная или внешняя ошибка генерации"""

class GenerationConfigurationError(RuntimeError):
    """Постоянная ошибка из-за настройки OpenAI"""

async def generate_post_text(
        news_summary: str,
        news_title: str = ''
) -> str:
    body = news_summary.strip()
    title = news_title.strip()

    if not body:
        raise ValueError('Нельзя сгенерировать пост из пустого текста')

    user_input = f'Загаловок: {title}\n\nТекст новости: {body}'

    try:
        response = await client.responses.create(
            model=settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=user_input,
            max_output_tokens=settings.openai_max_tokens,
            store=False
        )
    except AuthenticationError as ext:
        logger.error(f"OpenAI Auth error: {ext}")
        raise GenerationConfigurationError('OpenAI отклонил API-key')
    except (RateLimitError, APIConnectionError, APITimeoutError) as ext:
        logger.warning(f"OpenAI rate limit/connection error: {ext}")
        raise GenerationError('Временная ошибка OpenAI')
    except APIStatusError as ext:
        logger.error(f"OpenAI API status error: {ext}")
        raise GenerationError('Ошибка сервиса OpenAI')

    text = await response.output_text.strip()

    if len(text) > 800:
        raise GenerationError(
            f'OpenAI превысил лимит длины {len(text)} символов'
        )
    return text
