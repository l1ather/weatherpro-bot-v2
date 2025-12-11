import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import weather, location, forecast, favorites, errors
from middlewares.throttling import ThrottlingMiddleware
from middlewares.logging import LoggingMiddleware, StatisticsMiddleware, UserActivityMiddleware
from services.cache import RedisCache
from database.models import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("=" * 50)
    logger.info("🚀 Запуск WeatherPro Bot v2.0")
    logger.info("=" * 50)
    
    # Инициализация БД
    logger.info("📦 Инициализация базы данных...")
    SessionLocal = init_db()
    session = SessionLocal()
    session.close()
    logger.info("✅ База данных готова")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("=" * 50)
    logger.info("🛑 Остановка WeatherPro Bot")
    logger.info("=" * 50)
    
    await bot.session.close()


async def main():
    """Инициализация и запуск бота"""
    
    # Инициализация бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Инициализация кеша
    cache = RedisCache()
    await cache.connect()
    
    # Инициализация middleware
    stats_middleware = StatisticsMiddleware()
    
    # Регистрация middleware (порядок важен!)
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(UserActivityMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1))
    dp.message.middleware(stats_middleware)
    
    dp.callback_query.middleware(LoggingMiddleware())
    dp.callback_query.middleware(UserActivityMiddleware())
    
    # Регистрация роутеров
    dp.include_router(weather.router)
    dp.include_router(location.router)
    dp.include_router(forecast.router)
    dp.include_router(favorites.router)
    dp.include_router(errors.router)
    
    # Передача зависимостей
    dp.workflow_data.update({
        'cache': cache,
        'stats': stats_middleware
    })
    
    # События запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(lambda: on_shutdown(bot))
    
    try:
        await on_startup()
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info(f"🔗 Bot username: @{(await bot.get_me()).username}")
        
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    
    finally:
        await cache.close()
        logger.info("👋 Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}", exc_info=True)