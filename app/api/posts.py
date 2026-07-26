from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_session
from app.models import Post, PostStatus
from app.schemas import PostResponse
from typing import Optional

from app.repository.post_repo import PostRepository

router = APIRouter(prefix='/api/v1/posts', tags=['Posts'])


@router.get('/', response_model=list[PostResponse],
            summary='Получить историю постов',
            response_description='Список постов')
async def list_posts(
        status: Optional[str] = Query(None, description='Фильтр по статусу поста: pending, generated, published, failed, skipped'),
        limit: int = Query(20, ge=1, le=100, description='Максимальное количество возвращаемых записей (пагинация)'),
        offset: int = Query(0, ge=0, description='Смещение для пагинации'),
        session: AsyncSession = Depends(get_session),
):
    """
    Возвращает историю сгенерированных и опубликованных постов с поддержкой пагинации и фильтрации.

    - **status**: Фильтрация по состоянию поста (`pending`, `generated`, `published`, `failed`, `skipped`).
    - Записи отсортированы по убыванию даты создания (самые свежие сверху).
    """
    stmt = select(Post).order_by(desc(Post.created_at)).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Post.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get('/stats',
            summary='Получить статистику по постам',
            response_description='Агрегированная статистика')
async def get_posts_stats(
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает сводную статистику по постам (общее количество и разбивка по статусам).
    """
    return await PostRepository(session).get_stats()


@router.get('/{post_id}', response_model=PostResponse,
            summary='Получить пост по ID',
            response_description='Информация о посте')
async def get_post(
        post_id: int = Path(..., description='Уникальный идентификатор поста'),
        session: AsyncSession = Depends(get_session),
):
    """
    Возвращает детальные данные о конкретном посте по его идентификатору.
    """
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f'Пост {post_id} не найден')
    return post





