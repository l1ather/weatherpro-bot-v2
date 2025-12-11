import json
import logging
from typing import Any, Optional
from redis.asyncio import Redis
from config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Сервис кеширования на Redis"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("✅ Redis подключен")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Redis: {e}")
            self.redis = None
    
    async def close(self):
        """Закрытие соединения"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis соединение закрыто")
    
    async def get(self, key: str) -> Optional[dict]:
        """Получить данные из кеша"""
        if not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                logger.info(f"📦 Кеш HIT: {key}")
                return json.loads(data)
            logger.info(f"🔍 Кеш MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Ошибка чтения кеша: {e}")
            return None
    
    async def set(self, key: str, value: dict, ttl: int = settings.CACHE_TTL):
        """Сохранить данные в кеш"""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            logger.info(f"💾 Данные закешированы: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Ошибка записи в кеш: {e}")
    
    async def delete(self, pattern: str):
        """Удалить ключи по паттерну"""
        if not self.redis:
            return
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"🗑️ Удалено ключей: {len(keys)}")
        except Exception as e:
            logger.error(f"Ошибка удаления из кеша: {e}")
    
    def make_key(self, prefix: str, *args) -> str:
        """Создать ключ кеша"""
        return f"{prefix}:{':'.join(str(arg).lower() for arg in args)}"