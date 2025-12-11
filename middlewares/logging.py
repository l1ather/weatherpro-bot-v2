import logging
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех запросов"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        start_time = time.time()
        
        # Определяем тип события
        if isinstance(event, Message):
            user = event.from_user
            event_type = "message"
            event_text = event.text or "[no text]"
            
            if event.location:
                event_text = f"[location: {event.location.latitude}, {event.location.longitude}]"
            elif event.photo:
                event_text = "[photo]"
            elif event.document:
                event_text = "[document]"
        
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            event_type = "callback"
            event_text = event.data
        
        else:
            return await handler(event, data)
        
        # Логируем входящий запрос
        logger.info(
            f"📥 {event_type.upper()} | "
            f"User: @{user.username or 'Unknown'} ({user.id}) | "
            f"Text: {event_text[:50]}"
        )
        
        try:
            # Выполняем обработчик
            result = await handler(event, data)
            
            # Вычисляем время обработки
            processing_time = time.time() - start_time
            
            # Логируем успешную обработку
            logger.info(
                f"✅ {event_type.upper()} processed | "
                f"User: {user.id} | "
                f"Time: {processing_time:.3f}s"
            )
            
            return result
        
        except Exception as e:
            # Логируем ошибку
            processing_time = time.time() - start_time
            
            logger.error(
                f"❌ {event_type.upper()} error | "
                f"User: {user.id} | "
                f"Time: {processing_time:.3f}s | "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            raise


class StatisticsMiddleware(BaseMiddleware):
    """Middleware для сбора статистики"""
    
    def __init__(self):
        self.stats = {
            'total_messages': 0,
            'total_callbacks': 0,
            'unique_users': set(),
            'commands': {},
            'errors': 0
        }
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = event.from_user.id
        self.stats['unique_users'].add(user_id)
        
        # Статистика по типу события
        if isinstance(event, Message):
            self.stats['total_messages'] += 1
            
            # Статистика команд
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
        """Получить статистику"""
        return {
            'total_messages': self.stats['total_messages'],
            'total_callbacks': self.stats['total_callbacks'],
            'unique_users': len(self.stats['unique_users']),
            'commands': self.stats['commands'],
            'errors': self.stats['errors']
        }


class UserActivityMiddleware(BaseMiddleware):
    """Middleware для отслеживания активности пользователей"""

async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        
        # Обновляем информацию о пользователе в БД
        from database.models import init_db
        from database.crud import UserCRUD
        
        SessionLocal = init_db()
        session = SessionLocal()
        
        try:
            user_data = {
                'username': event.from_user.username,
                'first_name': event.from_user.first_name,
                'last_name': event.from_user.last_name,
                'language_code': event.from_user.language_code
            }
            
            UserCRUD.get_or_create(
                session,
                event.from_user.id,
                **user_data
            )
            
            return await handler(event, data)
        
        finally:
            session.close()