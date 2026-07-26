import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.telegram.client import telegram_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/auth', tags=['Telegram Auth'])

# временное состояние между send-code и sign-in (выполняется один раз, in-memory достаточно)
_auth_state: dict = {}


class SendCodeRequest(BaseModel):
    phone: str


class SignInRequest(BaseModel):
    phone: str
    code: str


class AuthStatusResponse(BaseModel):
    session_exists: bool
    is_authorized: bool
    username: str | None = None


@router.get(
    '/status',
    response_model=AuthStatusResponse,
    summary='Статус Telegram-сесии',
    response_description='Создан ли файл сесии и авторизован ли аккаунт',
)
async def get_auth_status() -> AuthStatusResponse:
    """Проверяет наличие файла сессии Telethon и авторизацию учетной записи"""
    session_file = Path(f'{settings.tg_session_name}.session')
    session_exists = session_file.exists()

    is_authorized = False
    username = None

    if session_exists:
        try:
            await telegram_client.connect()
            is_authorized = await telegram_client.is_user_authorized()
            if is_authorized:
                me = await telegram_client.get_me()
                username = me.username if me else None
        except Exception as exc:
            logger.warning(f'[AUTH] Не удалось проверить авторизацию: {exc}')

    return AuthStatusResponse(
        session_exists=session_exists,
        is_authorized=is_authorized,
        username=username,
    )


@router.post(
    '/send-code',
    summary='Отправить код авторизации',
    response_description='Подтверждение отправки кода',
)
async def send_code(data: SendCodeRequest) -> dict:
    """
    Отправляет код подтверждения в Telegram на указанный номер телефона.
    Номер телефона в формате: +380XXXXXXXXX
    """
    if await telegram_client.is_user_authorized():
        raise HTTPException(status_code=409, detail='Сессия уже существует и авторизована')

    try:
        await telegram_client.connect()
        result = await telegram_client.send_code_request(data.phone)
        _auth_state['phone'] = data.phone
        _auth_state['phone_code_hash'] = result.phone_code_hash
        logger.info(f'[AUTH] Код отправлен на {data.phone}')
        return {'message': f'Код отправлен на {data.phone}. Теперь вызови /sign-in'}
    except Exception as exc:
        logger.error(f'[AUTH] Ошибка отправки кода: {exc}')
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    '/sign-in',
    summary='Подтвердить код и сохранить сессию',
    response_description='Результат авторизации',
)
async def sign_in(data: SignInRequest) -> dict:
    """
    Завершает авторизацию в Telegram с помощью кода из SMS/приложения.
    Сохраняет сессию в файл — после этого перезапуск не требуется.
    """
    if 'phone_code_hash' not in _auth_state:
        raise HTTPException(
            status_code=400,
            detail='Сначала вызовите /send-code для получения кода'
        )

    try:
        await telegram_client.sign_in(
            phone=_auth_state['phone'],
            code=data.code,
            phone_code_hash=_auth_state['phone_code_hash'],
        )
        _auth_state.clear()

        me = await telegram_client.get_me()
        username = me.username if me else "неизвестно"
        logger.info(f'[AUTH] Успешная авторизация как @{username}')
        return {'message': f'Авторизован как @{username}. Сессия сохранена.', 'username': username}

    except Exception as exc:
        logger.error(f'[AUTH] Ошибка авторизации: {exc}')
        raise HTTPException(status_code=400, detail=str(exc))
