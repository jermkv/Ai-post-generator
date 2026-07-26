from typing import Literal

from app.ai.client import ai_client, GenerationError

SYSTEM_PROMPT = """
Ты - редактор русскоязычного Telegram-канала об IT и технологиях
Преобразуй переданную мысль в самостоятельный короткий пост

Правила:
1. Пиши только на русском языке.
2. Используй факты из входного текста; ничего не придумывай
3. Объем - 2-4 коротких предложения, не более 600 символов
4. Начни с 1-2 уместных emoji
5. Сохрани важные названия продуктов, компаний и технологий
6. Не используй Markdown, HTML разметку
7. В конце добавь короткий вопрос читателю, если он нужен
8. Верни только готовый текст поста
""".strip()


class PostGenerator:
    def __init__(self, client=ai_client):
        self._client = client

    async def generate_post_text(
            self,
            news_summary: str,
            news_title: str = '',
            provider: Literal['openai', 'gemini'] = 'gemini'
    ) -> str:
        body = news_summary.strip()
        title = news_title.strip()

        if not body:
            raise ValueError('Нельзя сгенерировать пост из пустого текста')

        user_input = f'Заголовок: {title}\n\nТекст новости: {body}'

        text = await self._client.generate(
            prompt=user_input,
            system_instruction=SYSTEM_PROMPT,
            provider=provider
        )

        if len(text) > 800:
            raise GenerationError(
                f'{provider.upper()} превысил лимит длины {len(text)} символов'
            )

        return text


post_generator = PostGenerator()