from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: Literal['rss', 'telegram']
    url: str = Field(..., min_length=1, max_length=500)
    enabled: bool = Field(default=True)

    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v: str, info) -> str:
        value = v.strip()
        source_type = info.data.get('source_type')
        if source_type == 'rss' and not value.startswith(('http://', 'https://')):
            raise ValueError('URL для RSS-источника должен начинаться с http/https')
        if source_type == 'telegram' and not value.startswith('@'):
            raise ValueError('Username для Telegram должен начинаться с @')
        return value


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    enabled: Optional[bool] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    url: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    model_config = {'from_attributes': True}


class KeywordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    pattern: Optional[str] = Field(None, max_length=200)
    enabled: bool = Field(default=True)

    @field_validator('word')
    @classmethod
    def lowercase_word(cls, v: str) -> str:
        value = v.lower().strip()
        if not value:
            raise ValueError('Ключевое слово не может быть пустым')
        return value


class KeywordResponse(BaseModel):
    id: int
    word: str
    pattern: Optional[str]
    enabled: bool
    created_at: datetime
    model_config = {'from_attributes': True}


class NewsItemResponse(BaseModel):
    id: str
    title: str
    url: Optional[str]
    summary: str
    raw_text: Optional[str]
    source_id: int
    source_name: str
    published_at: datetime
    collected_at: datetime
    is_processed: bool
    model_config = {'from_attributes': True}


class PostResponse(BaseModel):
    id: int
    news_id: str
    generated_text: str
    status: str
    published_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    model_config = {'from_attributes': True}


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class MessageResponse(BaseModel):
    message: str


class GenerationRequest(BaseModel):
    title: str = Field(..., max_length=500)
    body: str = Field(..., min_length=20, max_length=20_000)


class GenerationResponse(BaseModel):
    generated_text: str
    char_count: int
