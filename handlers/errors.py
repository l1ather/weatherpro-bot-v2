import logging
from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()
logger = logging.getLogger(__name__)


@router.error()
async def error_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок"""
    logger.error(f"Критическая ошибка: {event.exception}", exc_info=True)
    
    if event.update.message:
        try:
            await event.update.message.answer(
                "😔 <b>Произошла непредвиденная ошибка</b>\n\n"
                "Попробуйте повторить запрос через несколько секунд"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")