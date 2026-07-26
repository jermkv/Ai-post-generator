def main():
    pass
import asyncio
import logging
from celery_worker import celery_app
from app.database import AsyncSessionLocal
from app.repository.news_repo import NewsRepository
from app.repository.post_repo import PostRepository
from app.ai.generator import post_generator

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name='tasks.generate_post_task',
    max_retries=3,
    default_retry_delay=60,
    time_limit=120
)
def generate_post_task(self, news_id: str):
    async def _run():
        async with AsyncSessionLocal() as session:
            news_repo = NewsRepository(session)
            post_repo = PostRepository(session)

            news_item = await news_repo.get_newsitem_by_id(news_id)
            if not news_item:
                logger.warning(f"[GENERATION] Новость {news_id} не найдена.")
                return

            # Защита от двойной генерации
            if await post_repo.exists_for_news(news_id):
                logger.warning(f"[GENERATION] Пост для {news_id} уже существует.")
                await news_repo.mark_processed(news_id)
                return

            # Вызываем AI
            text_to_summarize = news_item.raw_text or news_item.summary
            generated_text = await post_generator.generate_post_text(
                news_summary=text_to_summarize,
                news_title=news_item.title,
                provider='gemini' # или 'openai', если вывел в настройки
            )

            # Сохраняем пост
            post = await post_repo.create(news_id=news_id, generated_text=generated_text)

            # Помечаем новость как полностью обработанную
            await news_repo.mark_processed(news_id)
            logger.info(f"[GENERATION] Пост {post.id} сгенерирован для новости {news_id}.")

            # Передаем эстафету публикации
            from app.tasks.publishing import publish_post_task
            publish_post_task.delay(post_id=post.id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"[GENERATION] Ошибка для news_id={news_id}: {exc}", exc_info=True)
        # В случае ошибки генерации можно реализовать логику смены статуса на FAILED
        raise self.retry(exc=exc)