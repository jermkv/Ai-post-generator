from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.repository.keyword_repo import KeywordRepository
from app.schemas import KeywordCreate, KeywordResponse, MessageResponse
from fastapi import APIRouter, Depends, HTTPException, status, Path

router = APIRouter(prefix='/api/v1/keywords', tags=['Keywords'])


@router.post('/', response_model=KeywordResponse,
             status_code=status.HTTP_201_CREATED,
             summary='Добавить ключевое слово',
             response_description='Созданное ключевое слово')
async def create_keyword(
        data: KeywordCreate,
        session: AsyncSession = Depends(get_session),
):
    """
    Добавляет новое ключевое слово для фильтрации входящих новостей.

    - **word**: Ключевое слово или фраза (например, 'Python', 'AI', 'GPT-4')
    - **pattern**: Дополнительное регулярное выражение или шаблон (опционально)
    """
    repo = KeywordRepository(session)
    if await repo.exists(data.word):
        raise HTTPException(status_code=409, detail=f'Слово "{data.word}" уже есть')
    return await repo.create(data)


@router.get('/', response_model=list[KeywordResponse],
            summary='Получить список ключевых слов',
            response_description='Список ключевых слов')
async def list_keywords(session: AsyncSession = Depends(get_session)):
    """
    Возвращает полный список всех ключевых слов, используемых для фильтрации новостей.
    """
    return await KeywordRepository(session).get_all()


@router.delete('/{keyword_id}', response_model=MessageResponse,
               summary='Удалить ключевое слово',
               response_description='Результат удаления')
async def delete_keyword(
        keyword_id: int = Path(..., description='Уникальный идентификатор ключевого слова'),
        session: AsyncSession = Depends(get_session),
):
    """
    Удаляет ключевое слово из базы данных по его идентификатору.
    """
    deleted = await KeywordRepository(session).delete(keyword_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Ключевое слово не найдено')
    return MessageResponse(message=f'Слово {keyword_id} удалено')

