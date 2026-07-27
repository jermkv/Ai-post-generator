import logging
from telethon.errors import ChatWriteForbiddenError
from app.config import settings
from app.telegram.client import get_telegram_client

logger = logging.getLogger(__name__)

TELEGRAM_TEXT_LIMIT = 4096

class PublishPermissionError(RuntimeError):
    """Аккаунт не может писать в целевой канал"""


async def publish_to_channel(text: str) -> int:
    clean_text = text.strip()

    if not clean_text:
        raise ValueError('Нельзя публиковать пустой текст')

    if len(clean_text) > TELEGRAM_TEXT_LIMIT:
        raise ValueError(
            f'Текст длиннее лимита Telegram {len(clean_text)}'
        )

    client = await get_telegram_client()

    try:
        message = await client.send_message(
            entity= int(settings.tg_target_channel),
            message=clean_text,
            parse_mode=None
        )
    except ChatWriteForbiddenError as ext:
        raise PublishPermissionError(
            f'Нет прав писать в {settings.tg_target_channel}'
        )

    return message.id