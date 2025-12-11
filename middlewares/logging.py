import logging
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


# ===============================================
# Middleware для логирования всех запросов
# ===============================================
class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех входящих сообщений и callback'ов"""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.time()

        user = getattr(event, "from_user", None)
        if isinstance(event, Message):
            event_type = "message"
            event_text = event.text or "[no text]"
            if event.location:
                event_text = f"[location: {event.location.latitude}, {event.location.longitude}]"
            elif event.photo:
                event_text = "[photo]"
            elif event.document:
                event_text = "[document]"
        elif isinstance(event, CallbackQuery):
            event_type = "callback"
            event_text = event.data
        else:
            return await handler(event, data)

        # Логируем входящее событие
        logger.info(
            f"📥 {event_type.upper()} | "
            f"User: @{getattr(user, 'username', 'Unknown')} ({getattr(user, 'id', 'N/A')}) | "
            f"Text: {str(event_text)[:50]}"
        )

        try:
            result = await handler(event, data)
            processing_time = time.time() - start_time
            logger.info(
                f"✅ {event_type.upper()} processed | "
                f"User: {getattr(user, 'id', 'N/A')} | "
                f"Time: {processing_time:.3f}s"
            )
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"❌ {event_type.upper()} error | "
                f"User: {getattr(user, 'id', 'N/A')} | "
                f"Time: {processing_time:.3f}s | "
                f"Error: {str(e)}",
                exc_info=True
            )
            raise


# ===============================================
# Middleware для сбора статистики
# ===============================================
class StatisticsMiddleware(BaseMiddleware):
    """Middleware для подсчёта статистики бота"""

    def __init__(self):
        super().__init__()
        self.stats = {
            'total_messages': 0,
            'total_callbacks': 0,
            'unique_users': set(),
            'commands': {},
            'errors': 0
        }

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        user_id = getattr(event.from_user, "id", None)
        if user_id:
            self.stats['unique_users'].add(user_id)

        if isinstance(event, Message):
            self.stats['total_messages'] += 1
            if event.text and event.text.startswith('/'):
                command = event.text.split()[0]
                self.stats['commands'][command] = self.stats['commands'].get(command, 0) + 1
        elif isinstance(event, CallbackQuery):
            self.stats['total_callbacks'] += 1

        try:
            return await handler(event, data)
        except Exception:
            self.stats['errors'] += 1
            raise

    def get_stats(self) -> dict:
        return {
            'total_messages': self.stats['total_messages'],
            'total_callbacks': self.stats['total_callbacks'],
            'unique_users': len(self.stats['unique_users']),
            'commands': self.stats['commands'],
            'errors': self.stats['errors']
        }


# ===============================================
# Middleware для отслеживания активности пользователей
# ===============================================
class UserActivityMiddleware(BaseMiddleware):
    """Middleware для обновления информации о пользователях в БД"""

    async def __call__(
        self,
        handler: Callable[..., Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:

        user = getattr(event, "from_user", None)
        if user:
            try:
                # Локальный импорт, чтобы избежать циклических зависимостей
                from database.models import init_db
                from database.crud import UserCRUD

                SessionLocal = init_db()
                session = SessionLocal()

                user_data = {
                    'username': getattr(user, "username", None),
                    'first_name': getattr(user, "first_name", None),
                    'last_name': getattr(user, "last_name", None),
                    'language_code': getattr(user, "language_code", None)
                }

                UserCRUD.get_or_create(
                    session,
                    getattr(user, "id", None),
                    **user_data
                )

            finally:
                session.close()

        return await handler(event, data)