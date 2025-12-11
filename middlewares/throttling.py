from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
import time


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, rate_limit: float = 1.0):
        """
        :param rate_limit: минимальное время между запросами (секунды)
        """
        self.rate_limit = rate_limit
        self.user_timings: Dict[int, float] = {}
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = time.time()
        
        # Проверяем последний запрос пользователя
        if user_id in self.user_timings:
            time_passed = current_time - self.user_timings[user_id]
            
            if time_passed < self.rate_limit:
                await event.answer(
                    "⏱ Пожалуйста, подождите немного перед следующим запросом"
                )
                return
        
        # Обновляем время последнего запроса
        self.user_timings[user_id] = current_time
        
        return await handler(event, data)