from datetime import timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert  # для INSERT ON CONFLICT
from app.models import NewsItem
from app.utils.datetime import utc_now_naive
from typing import Optional


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_if_new(self, news_data: dict) -> bool:
        """
        Сохраняет новость если её ещё нет в БД.
        Возвращает True если сохранено (новая), False если дубликат.

        Используем INSERT ... ON CONFLICT DO NOTHING — это атомарная
        операция PostgreSQL. Безопаснее чем SELECT + INSERT:
        - нет race condition при параллельных вставках
        - один запрос вместо двух
        - эффективнее при высокой частоте дублей
        """
        stmt = (
            insert(NewsItem)
            .values(**news_data)
            .on_conflict_do_nothing(index_elements=['id'])  # id = хэш URL
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        # rowcount == 1 значит строка вставлена (новая новость)
        # rowcount == 0 значит конфликт — новость уже была
        return result.rowcount == 1

    async def save_batch(self, news_list: list[dict]) -> int:
        """
        Сохраняет пакет новостей. Возвращает количество новых (не дублей).
        Используется после одного запуска парсера.
        """
        saved = 0
        for news_data in news_list:
            is_new = await self.save_if_new(news_data)
            if is_new:
                saved += 1
        return saved

    async def get_unprocessed(
            self,
            limit: int = 50,
            max_age_hours: int = 24,
    ) -> list[NewsItem]:
        """
        Возвращает необработанные новости для генерации постов.
        max_age_hours — не берём новости старше N часов.
        Старые новости уже неактуальны для Telegram-канала.
        """
        cutoff = utc_now_naive() - timedelta(hours=max_age_hours)
        result = await self.session.execute(
            select(NewsItem)
            .where(and_(
                NewsItem.is_processed == False,
                NewsItem.published_at >= cutoff,
            ))
            .order_by(NewsItem.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_processed(self, news_id: str) -> None:
        """Помечаем новость обработанной после успешной генерации поста."""
        news = await self.session.get(NewsItem, news_id)
        if news:
            news.is_processed = True
            await self.session.commit()

    async def get_all_newsitems(
            self,
            is_processed: Optional[bool] = None,
            source_id: Optional[int] = None,
            limit: int = 20,
            offset: int = 0
    ) -> list[NewsItem]:
        """Возвращает список собранных новостей с фильтрацией и пагинацией."""
        stmt = select(NewsItem).order_by(NewsItem.published_at.desc()).limit(limit).offset(offset)
        conditions = []
        if is_processed is not None:
            conditions.append(NewsItem.is_processed == is_processed)
        if source_id is not None:
            conditions.append(NewsItem.source_id == source_id)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_newsitem_by_id(self, news_id: str) -> Optional[NewsItem]:
        """Возвращает новость по ее идентификатору."""
        return await self.session.get(NewsItem, news_id)

