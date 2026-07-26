from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_session
from app.repository.news_repo import NewsRepository
from app.schemas import NewsItemResponse

router = APIRouter(prefix='/api/v1/news', tags=['News'])


@router.get('/', response_model=list[NewsItemResponse],
            summary='Получить список собранных новостей',
            response_description='Список сырых новостей')
async def list_news(
        is_processed: Optional[bool] = Query(None, description='Фильтр: обработана ли новость в пост (true/false)'),
        source_id: Optional[int] = Query(None, description='Фильтр по ID источника'),
        limit: int = Query(20, ge=1, le=100, description='Максимальное количество записей (пагинация)'),
        offset: int = Query(0, ge=0, description='Смещение для пагинации'),
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает список всех сырых новостей, собранных парсерами из RSS-лент и Telegram-каналов.

    - **is_processed**: Можно отфильтровать еще не обработанные новости (`false`) или уже превращенные в пости (`true`).
    - **source_id**: Фильтрация по конкретному источнику.
    - Записи отсортированы по дате публикации (самые свежие новости сверху).
    """
    repo = NewsRepository(session)
    return await repo.get_all_newsitems(
        is_processed=is_processed,
        source_id=source_id,
        limit=limit,
        offset=offset
    )


@router.get('/{news_id}', response_model=NewsItemResponse,
            summary='Получить новость по ID',
            response_description='Информация о новости')
async def get_by_id(
        news_id: str = Path(..., description='Уникальный MD5-хеш идентификатор новости'),
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает детальную информацию о конкретной собранной новости по её уникальному идентификатору (MD5-хеш).
    """
    repo = NewsRepository(session)
    news = await repo.get_newsitem_by_id(news_id)
    if news is None:
        raise HTTPException(status_code=404, detail=f'Новость с ID {news_id} не найдена')
    return news
