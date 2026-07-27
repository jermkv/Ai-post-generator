import logging
from collections import Counter
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsItem, Source
from app.repository.keyword_repo import KeywordRepository
from app.repository.news_repo import NewsRepository

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 100


@dataclass
class FilterBatch:
    accepted: list[NewsItem] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    reasons: Counter[str] = field(default_factory=Counter)


class FilterService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Кэш для отлова дубликатов контента (одинаковых текстов) в рамках одного запуска
        self._seen_content_hashes = set()

    async def filter_news(self, items: list[NewsItem]) -> FilterBatch:
        result = FilterBatch()

        if not items:
            return result

        # 1. Получаем активные ключевые слова из БД
        keyword_repo = KeywordRepository(self.session)
        news_repo = NewsRepository(self.session)
        
        active_keywords = await keyword_repo.get_all_enabled()
        kw_list = [kw.lower() for kw in active_keywords]

        for item in items:
            # Собираем весь текст новости в одну строку для поиска
            full_text = f"{item.title} {item.summary} {item.raw_text or ''}".lower()

            # --- ПРОВЕРКА 1: Дубликаты по тексту ---
            # Title и URL уже защищены на уровне БД. Здесь ловим идентичные пресс-релизы.
            content_hash = hash(full_text)
            if content_hash in self._seen_content_hashes:
                result.rejected_ids.append(item.id)
                result.reasons["content_duplicate"] += 1
                continue
            self._seen_content_hashes.add(content_hash)

            # --- ПРОВЕРКА 2: Длина текста ---
            if len(full_text) < MIN_TEXT_LENGTH:
                result.rejected_ids.append(item.id)
                result.reasons["too_short"] += 1
                continue

            # --- ПРОВЕРКА 3: Источник (Source) ---
            # Проверяем, не отключил ли админ этот источник пока новость лежала в очереди
            if not await self._is_source_enabled(item.source_id):
                result.rejected_ids.append(item.id)
                result.reasons["source_disabled"] += 1
                continue

            # --- ПРОВЕРКА 4: Ключевые слова ---
            if kw_list:
                has_match = any(kw in full_text for kw in kw_list)
                if not has_match:
                    result.rejected_ids.append(item.id)
                    result.reasons["no_keywords_match"] += 1
                    continue

            # Если все проверки пройдены, добавляем в список на генерацию
            result.accepted.append(item)

        # --- ГЛАВНАЯ ЛОГИКА СЕРВИСА: помечаем отброшенные новости как "обработанные" ---
        # Чтобы оркестратор больше никогда не доставал их из БД
        for rejected_id in result.rejected_ids:
            await news_repo.mark_processed(rejected_id)

        logger.info(
            f"[FILTER] Принято: {len(result.accepted)}, "
            f"Отклонено: {len(result.rejected_ids)}. "
            f"Причины: {dict(result.reasons)}"
        )
        return result

    async def _is_source_enabled(self, source_id: int) -> bool:
        """Проверка статуса источника в БД (включен/выключен)."""
        source = await self.session.get(Source, source_id)
        return bool(source and source.enabled)