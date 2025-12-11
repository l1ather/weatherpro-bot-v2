import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from services.weather_api import WeatherAPI, CityNotFoundError, APITimeoutError
from services.formatter import WeatherFormatter
from keyboards.inline import get_city_actions_keyboard
from keyboards.main import get_main_keyboard
from utils.validators import CityValidator
from database.models import init_db
from database.crud import UserCRUD, WeatherRequestCRUD, FavoriteCityCRUD

router = Router()
logger = logging.getLogger(__name__)

# Инициализация БД
SessionLocal = init_db()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    session = SessionLocal()
    try:
        # Создаем или обновляем пользователя
        UserCRUD.get_or_create(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code
        )
        
        await message.answer(
            "👋 <b>Добро пожаловать в WeatherPro Bot v2!</b>\n\n"
            "Я помогу узнать погоду в любом городе мира.\n\n"
            "<b>🌟 Новые возможности:</b>\n"
            "⭐ Избранные города - быстрый доступ\n"
            "📊 Детальная информация с рекомендациями\n"
            "💾 История запросов\n"
            "🎨 Красивое оформление с emoji\n\n"
            "<b>Что я умею:</b>\n"
            "🌤 Показать текущую погоду\n"
            "📅 Прогноз на 5 дней\n"
            "📍 Погоду по вашей геолокации\n"
            "⭐ Сохранить избранные города\n\n"
            "Просто отправьте название города или выберите действие ниже 👇",
            reply_markup=get_main_keyboard()
        )
    
    finally:
        session.close()


@router.message(F.text == "🌤 Погода сейчас")
async def request_current_weather(message: Message):
    """Запрос текущей погоды"""
    await message.answer(
        "🌍 <b>Отправьте название города</b>\n\n"
        "Вы можете написать на русском или английском языке.\n\n"
        "<b>Примеры:</b>\n"
        "• <code>Москва</code>\n"
        "• <code>Санкт-Петербург</code>\n"
        "• <code>New York</code>\n"
        "• <code>London, UK</code>\n\n"
        "💡 <i>Для уточнения можно указать страну через запятую</i>"
    )


@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Команда помощи"""
    await message.answer(
        "<b>📖 Справка по использованию</b>\n\n"
        "<b>🌤 Текущая погода:</b>\n"
        "Отправьте название города для получения актуальной информации о погоде.\n\n"
        "<b>📅 Прогноз на 5 дней:</b>\n"
        "Нажмите кнопку и введите город для получения детального прогноза.\n\n"
        "<b>📍 Геолокация:</b>\n"
        "Используйте кнопку 'Отправить геолокацию' для определения погоды в вашем местоположении.\n\n"
        "<b>⭐ Избранные города:</b>\n"
        "Добавьте до 10 любимых городов для быстрого доступа к их погоде.\n\n"
        "<b>💡 Дополнительные возможности:</b>\n"
        "• Умные рекомендации по погоде\n"
        "• Кеширование для быстрых ответов\n"
        "• Детальная информация о влажности, ветре, давлении\n"
        "• Эмодзи-индикаторы температуры\n\n"
        "<b>🎯 Команды:</b>\n"
        "/start - Начало работы\n"
        "/help - Эта справка\n"
        "/favorites - Избранные города\n\n"
        "💾 <i>Данные кешируются на 1 час для экономии API-запросов</i>"
    )


@router.message(F.text & ~F.text.startswith('/'))
async def get_weather_by_city(message: Message, cache):
    """Получить погоду по названию города"""
    city = message.text.strip()
    
    # Игнорируем кнопки меню
    menu_buttons = ["🌤 Погода сейчас", "📅 Прогноз на 5 дней", "⭐ Избранное", "ℹ️ Помощь"]
    if city in menu_buttons:
        return
    
    # Валидация названия города
    sanitized_city = CityValidator.sanitize(city)
    
    if not sanitized_city:
        error_msg = CityValidator.get_error_message(city)
        await message.answer(
            f"❌ <b>Ошибка в названии города</b>\n\n"
            f"{error_msg}\n\n"
            "Попробуйте еще раз или отправьте /help для справки"
        )
        return
    
    session = SessionLocal()
    status_msg = await message.answer("🔍 Ищу информацию о погоде...")
    
    try:
        # Получаем или создаем пользователя
        user = UserCRUD.get_or_create(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        
        # Получаем погоду
        api = WeatherAPI(cache)
        weather = await api.get_current_weather(sanitized_city)
        
        # Логируем запрос
        WeatherRequestCRUD.create(
            session,
            user.id,
            weather['city'],
            'current',
            success=True
        )
        
        # Проверяем, в избранном ли город
        is_favorite = FavoriteCityCRUD.is_favorite(session, user.id, weather['city'])
        
        # Форматируем ответ
        text = WeatherFormatter.format_current_weather(weather)
        
        # Удаляем статусное сообщение
        await status_msg.delete()
        
        # Отправляем результат
        await message.answer(
            text,
            reply_markup=get_city_actions_keyboard(weather['city'], is_favorite)
        )
        
        logger.info(f"✅ Погода отправлена: {weather['city']} для пользователя {user.id}")
        
    except CityNotFoundError:
        await status_msg.edit_text(
            "❌ <b>Город не найден</b>\n\n"
            "Проверьте правильность написания или попробуйте:\n"
            "• Указать страну: <code>Springfield, US</code>\n"
            "• Использовать английское название\n"
            "• Проверить опечатки\n\n"
            "💡 Вы также можете отправить геолокацию для определения погоды"
        )
        
        # Логируем неудачный запрос
        if session:
            user = UserCRUD.get_or_create(session, message.from_user.id)
            WeatherRequestCRUD.create(session, user.id, sanitized_city, 'current', success=False)
    
    except APITimeoutError:
        await status_msg.edit_text(
            "⏱ <b>Превышено время ожидания</b>\n\n"
            "Сервис погоды временно недоступен.\n"
            "Попробуйте через несколько минут.\n\n"
            "🔄 Мы автоматически повторили запрос 3 раза"
        )
    
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}", exc_info=True)
        await status_msg.edit_text(
            "😔 <b>Произошла непредвиденная ошибка</b>\n\n"
            "Попробуйте еще раз через несколько секунд.\n"
            "Если ошибка повторяется, обратитесь к администратору."
        )
    
    finally:
        session.close()


@router.callback_query(F.data.startswith("current:"))
async def callback_current_weather(callback: CallbackQuery, cache):
    """Обработка callback для обновления текущей погоды"""
    city = callback.data.split(":", 1)[1]
    
    await callback.answer("🔄 Обновляю данные...")
    
    session = SessionLocal()
    try:
        api = WeatherAPI(cache)
        
        # Удаляем кеш для получения свежих данных
        cache_key = cache.make_key('weather', city)
        await cache.delete(cache_key)
        
        weather = await api.get_current_weather(city)
        
        # Логируем запрос
        user = UserCRUD.get_or_create(session, callback.from_user.id)
        WeatherRequestCRUD.create(session, user.id, weather['city'], 'current', success=True)
        
        # Проверяем избранное
        is_favorite = FavoriteCityCRUD.is_favorite(session, user.id, weather['city'])
        
        # Обновляем сообщение
        text = WeatherFormatter.format_current_weather(weather, from_cache=False)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_city_actions_keyboard(weather['city'], is_favorite)
        )
        
        logger.info(f"🔄 Погода обновлена: {weather['city']} для пользователя {user.id}")
        
    except CityNotFoundError:
        await callback.answer("❌ Город не найден", show_alert=True)
    
    except APITimeoutError:
        await callback.answer("⏱ Превышено время ожидания", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка обновления погоды: {e}", exc_info=True)
        await callback.answer("❌ Ошибка обновления", show_alert=True)
    
    finally:
        session.close()


@router.message(Command("history"))
async def show_history(message: Message):
    """Показать историю запросов пользователя"""
    session = SessionLocal()
    try:
        user = UserCRUD.get_or_create(session, message.from_user.id)
        history = WeatherRequestCRUD.get_user_history(session, user.id, limit=10)
        
        if not history:
            await message.answer(
                "📋 <b>История запросов пуста</b>\n\n"
                "Начните использовать бота, чтобы увидеть историю!"
            )
            return
        
        text = "📋 <b>Ваши последние запросы:</b>\n\n"
        
        for i, request in enumerate(history, 1):
            status = "✅" if request.success else "❌"
            date = request.created_at.strftime("%d.%m %H:%M")
            text += f"{i}. {status} {request.city_name} - {date}\n"
        
        await message.answer(text)
    
    finally:
        session.close()