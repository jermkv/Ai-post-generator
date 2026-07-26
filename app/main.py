import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.keywords import router as keywords_router
from app.api.posts import router as posts_router
from app.api.sources import router as sources_router
from app.api.generate import router as generate_router
from app.api.news import router as news_router
from app.config import settings
from app.database import engine


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Приложение запущено')
    yield
    await engine.dispose()
    logger.info('Соединения с БД закрыты')



app = FastAPI(
      title='AI News Bot API',
      description='Управление источниками, ключевыми словами и историей постов',
      version='1.0.0',
      lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(sources_router)
app.include_router(keywords_router)
app.include_router(news_router)
app.include_router(posts_router)
app.include_router(generate_router)

@app.get('/health', tags=['System'])
async def health_check():
    return {'status': 'ok', 'env': settings.app_env}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', reload=True)
