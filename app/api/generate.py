from fastapi import APIRouter, HTTPException
from app.ai.client import GenerationConfigurationError, GenerationError, generate_post_text
from app.schemas import GenerationRequest, GenerationResponse


router = APIRouter(prefix='/api/v1/generate', tags=['AI generation'])

@router.post('/', response_model=GenerationResponse,
             summary='Сгенерировать пост через AI (Предпросмотр)',
             response_description='Сгенерированный текст поста')
async def generate_preview(data: GenerationRequest) -> GenerationResponse:
    """
    Генерирует готовый текст поста для Telegram-канала на основе заголовка и краткого содержания новости через OpenAI API.

    Используется для ручного тестирования и предпросмотра результата генерации без сохранения в базу данных.
    """
    try:
        text = await generate_post_text(
            news_summary=data.body,
            news_title=data.title
        )
    except ValueError as ext:
        raise HTTPException(status_code=400, detail=str(ext))
    except GenerationConfigurationError as ext:
        raise HTTPException(status_code=503, detail=str(ext))
    except GenerationError as ext:
        raise HTTPException(status_code=502, detail=str(ext))

    return GenerationResponse(
        generated_text=text,
        char_count=len(text)
    )

