import asyncio
import logging
from celery_worker import celery_app
from app.database import AsyncSessionLocal
from app.repository.post_repo import PostRepository
from app.models import PostStatus
from app.telegram.publisher import publish_to_channel

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name='tasks.publish_post_task',
    max_retries=3,
    default_retry_delay=60,
    time_limit=60
)
def publish_post_task(self, post_id: int):
    async def _run():
        async with AsyncSessionLocal() as session:
            post_repo = PostRepository(session)
            post = await post_repo.get_by_id(post_id)

            if not post or post.status == PostStatus.PUBLISHED:
                logger.warning(f"[PUBLISHING] Пост {post_id} не найден или уже опубликован.")
                return

            try:
                await publish_to_channel(text=post.generated_text)

                # Обновляем статус
                await post_repo.update_status(post_id=post.id, status=PostStatus.PUBLISHED)
                logger.info(f"[PUBLISHING] Пост {post_id} успешно опубликован в Telegram.")

            except Exception as tg_exc:
                # Если ошибка телеграма, меняем статус на FAILED
                await post_repo.update_status(
                    post_id=post.id,
                    status=PostStatus.FAILED,
                    error_message=str(tg_exc)
                )
                raise tg_exc

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"[PUBLISHING] Ошибка публикации post_id={post_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)