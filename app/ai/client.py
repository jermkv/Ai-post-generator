import logging
from typing import Literal

from google import genai
from google.genai import types
from google.genai.errors import APIError

from openai import (
    AsyncOpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    APIStatusError,
)

from app.config import settings

logger = logging.getLogger(__name__)


class GenerationError(RuntimeError):
    """Временная или внешняя ошибка генерации (можно повторять retry)"""


class GenerationConfigurationError(RuntimeError):
    """Постоянная ошибка из-за настройки"""


class AIClient:
    def __init__(self):
        self._openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=30.0,
            max_retries=2
        )
        self._gemini_client = genai.Client(
            api_key=settings.gemini_api_key
        )

    async def generate(
            self,
            prompt: str,
            system_instruction: str,
            provider: Literal['openai', 'gemini'] = 'gemini'
    ) -> str:
        if provider == 'openai':
            return await self._generate_openai(prompt, system_instruction)
        elif provider == 'gemini':
            return await self._generate_gemini(prompt, system_instruction)
        else:
            raise ValueError(f'Неподдерживаемый провайдер: {provider}')

    async def _generate_openai(self, prompt: str, system_instruction: str) -> str:
        try:
            response = await self._openai_client.responses.create(
                model=settings.openai_model,
                instructions=system_instruction,
                input=prompt,
                max_output_tokens=settings.openai_max_tokens,
                store=False
            )
            return response.output_text.strip()
        except AuthenticationError as ext:
            logger.error(f"OpenAI Auth error: {ext}")
            raise GenerationConfigurationError('OpenAI отклонил API-key')
        except (RateLimitError, APIConnectionError, APITimeoutError) as ext:
            logger.warning(f"OpenAI rate limit/connection error: {ext}")
            raise GenerationError('Временная ошибка OpenAI')
        except APIStatusError as ext:
            logger.error(f"OpenAI API status error: {ext}")
            raise GenerationError('Ошибка сервиса OpenAI')

    async def _generate_gemini(self, prompt: str, system_instruction: str) -> str:
        try:
            response = await self._gemini_client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=settings.gemini_max_tokens,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0,  # 0 = no thinking
                    ),
                ),
            )
            if not response.text:
                raise GenerationError('Gemini вернул пустой ответ')
            return response.text.strip()
        except APIError as ext:
            if ext.code == 429:
                logger.warning(f"Gemini rate limit error (429): {ext}")
                raise GenerationError('Превышен лимит запросов Gemini (Rate limit)')

            if ext.code in (401, 403):
                logger.error(f"Gemini Auth error ({ext.code}): {ext}")
                raise GenerationConfigurationError('Gemini отклонил API-key')

            logger.error(f"Gemini API error: {ext}")
            raise GenerationError(f'Ошибка сервиса Gemini: {ext.message}')
        except Exception as ext:
            logger.error(f"Unexpected Gemini error: {ext}")
            raise GenerationError('Временная ошибка Gemini')


ai_client = AIClient()