import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.weather_api import WeatherAPI, CityNotFoundError, APITimeoutError
from keyboards.main import get_forecast_keyboard

router = Router()
logger = logging.getLogger(__name__)

WEATHER_EMOJI = {
    '01d': '☀️', '01n': '🌙',
    '02d': '⛅', '02n': '☁️',
    '03d': '☁️', '03n': '☁️',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧', '09n': '🌧',
    '10d': '🌦', '10n': '🌧',
    '11d': '⛈', '11n': '⛈',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫', '50n': '🌫',
}

DAYS_RU = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье'
}


@router.message(F.text == "📅 Прогноз на 5 дней")
async def request_forecast(message: Message):
    """Запрос прогноза на 5 дней"""
    await message.answer(
        "📅 Отправьте название города для получения прогноза на 5 дней\n\n"
        "Например: <code>Москва</code> или <code>Paris</code>"
    )


@router.callback_query(F.data.startswith("forecast:"))
async def callback_forecast(callback: CallbackQuery, cache):
    """Обработка callback для прогноза"""
    city = callback.data.split(":", 1)[1]
    
    await callback.answer("📊 Загружаю прогноз...")
    
    try:
        api = WeatherAPI(cache)
        forecast = await api.get_forecast(city)
        
        if not forecast:
            await callback.answer("❌ Не удалось получить прогноз", show_alert=True)
            return
        
        text = f"📅 <b>Прогноз погоды для города {city}</b>\n\n"
        
        for day_forecast in forecast:
            date = datetime.strptime(day_forecast['date'], '%Y-%m-%d')
            day_name = DAYS_RU[date.weekday()]
            date_str = date.strftime('%d.%m')
            
            emoji = WEATHER_EMOJI.get(day_forecast['icon'], '🌡')
            
            text += (
                f"{emoji} <b>{day_name}, {date_str}</b>\n"
                f"   🌡 {day_forecast['temp']:+d}°C "
                f"(↓{day_forecast['temp_min']:+d}° ↑{day_forecast['temp_max']:+d}°)\n"
                f"   📝 {day_forecast['description']}\n"
                f"   💧 Влажность: {day_forecast['humidity']}%\n"
                f"   🌪 Ветер: {day_forecast['wind_speed']} м/с\n\n"
            )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_forecast_keyboard(city)
        )
        
    except CityNotFoundError:
        await callback.answer("❌ Город не найден", show_alert=True)
    
    except APITimeoutError:
        await callback.answer("⏱ Превышено время ожидания", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка получения прогноза: {e}")
        await callback.answer("❌ Ошибка получения прогноза", show_alert=True)