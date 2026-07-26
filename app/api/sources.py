from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.repository.source_repo import SourceRepository
from app.schemas import SourceCreate, SourceUpdate, SourceResponse, MessageResponse


router = APIRouter(prefix='/api/v1/sources', tags=['Sources'])


@router.post('/', response_model=SourceResponse,
             status_code=status.HTTP_201_CREATED,
             summary='Добавить источник новостей',
             response_description='Созданный источник новостей')
async def create_source(
        data: SourceCreate,
        session: AsyncSession = Depends(get_session)
):
    """
    Добавляет новый источник новостей (RSS-ленту или Telegram-канал).

    - **name**: Название источника (например, 'Habr Python' или 'TechNews')
    - **source_type**: Тип источника (`rss` или `telegram`)
    - **url**: Уникальная ссылка на RSS-ленту или username/URL Telegram-канала
    """
    repo = SourceRepository(session)
    if await repo.exists_by_url(data.url):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Источник с URL {data.url} уже существует'
        )
    source = await repo.create(data)
    return source


@router.get('/', response_model=list[SourceResponse],
            summary='Получить список источников',
            response_description='Список источников новостей')
async def get_list_sources(
        enabled_only: bool = Query(False, description='Фильтр: вернуть только активные источники'),
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает полный список всех зарегистрированных источников новостей.

    Поддерживает фильтрацию по активности (`enabled_only=true`).
    """
    repo = SourceRepository(session)
    return await repo.get_all(enabled_only=enabled_only)


@router.get('/{source_id}', response_model=SourceResponse,
            summary='Получить источник по ID',
            response_description='Информация об источнике')
async def get_source(
        source_id: int = Path(..., description='Уникальный идентификатор источника'),
        session: AsyncSession = Depends(get_session)
):
    """
    Возвращает подробную информацию об источнике новостей по его идентификатору.
    """
    repo = SourceRepository(session)
    source = await repo.get_by_id(source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Источник с id={source_id} не найден'
        )
    return source


@router.patch('/{source_id}', response_model=SourceResponse,
              summary='Обновить источник',
              response_description='Обновленные данные источника')
async def update_source(
    source_id: int = Path(..., description='Уникальный идентификатор источника'),
    data: SourceUpdate = ...,
    session: AsyncSession = Depends(get_session)
):
    """
    Частично обновляет данные существующего источника (название, URL, статус активности).
    """
    repo = SourceRepository(session)
    source = await repo.update(source_id=source_id, data=data)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Источник с id={source_id} не найден'
        )
    return source


@router.delete('/{source_id}', response_model=MessageResponse,
               summary='Удалить источник',
               response_description='Результат удаления')
async def delete_source(
    source_id: int = Path(..., description='Уникальный идентификатор источника'),
    session: AsyncSession = Depends(get_session)
):
    """
    Удаляет источник новостей из базы данных по его идентификатору.
    """
    repo = SourceRepository(session)
    deleted = await repo.delete(source_id=source_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Источник с id={source_id} не найден'
        )
    return MessageResponse(
        message=f'Источник {source_id} удален'
    )


