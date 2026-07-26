import asyncio
import logging
from celery_worker import celery_app
from app.database import AsyncSessionLocal
from app.repository.news_repo import NewsRepository
from app.services.filter import FilterService

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.run_pipeline')
def run_pipeline():
    async def _run():
        async with AsyncSessionLocal() as session:
            news_repo = NewsRepository(session)

            # 1. Берем новости за последние 24 часа, которые еще не обрабатывались
            unprocessed_news = await news_repo.get_unprocessed(limit=50, max_age_hours=24)

            if not unprocessed_news:
                logger.info("[PIPELINE] Нет новых новостей для обработки.")
                return 0

            # 2. Фильтруем новости. Фильтр сам пометит отбракованные как is_processed=True
            filter_service = FilterService(session)
            batch = await filter_service.filter_news(unprocessed_news)

            # 3. Отправляем прошедшие фильтр хорошие новости на генерацию
            from app.tasks.generation import generate_post_task
            for accepted_item in batch.accepted:
                generate_post_task.delay(news_id=accepted_item.id)

            logger.info(f"[PIPELINE] Отправлено на генерацию: {len(batch.accepted)} постов.")
            return len(batch.accepted)

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"[PIPELINE] Ошибка оркестрации: {exc}", exc_info=True)