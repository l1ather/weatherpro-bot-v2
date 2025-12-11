import logging
from aiogram import Router, F
from aiogram.types import Message
from services.weather_api import WeatherAPI, APITimeoutError
from keyboards.main import get_weather_keyboard

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


@router.message(F.location)
async def handle_location(message: Message, cache):
    """Обработка геолокации пользователя"""
    lat = message.location.latitude
    lon = message.location.longitude
    
    await message.answer("📍 Определяю погоду в вашем местоположении...")
    
    try:
        api = WeatherAPI(cache)
        weather = await api.get_weather_by_coords(lat, lon)
        
        emoji = WEATHER_EMOJI.get(weather['icon'], '🌡')
        
        text = (
            f"{emoji} <b>Погода в вашем местоположении</b>\n"
            f"📍 {weather['city']}, {weather['country']}\n\n"
            f"🌡 Температура: <b>{weather['temp']:+d}°C</b>\n"
            f"🤔 Ощущается как: {weather['feels_like']:+d}°C\n"
            f"📝 Описание: {weather['description']}\n\n"
            f"💧 Влажность: {weather['humidity']}%\n"
            f"🌪 Ветер: {weather['wind_speed']} м/с\n"
            f"🔽 Давление: {weather['pressure']} мм рт.ст.\n"
            f"☁️ Облачность: {weather['clouds']}%"
        )
        
        await message.answer(
            text,
            reply_markup=get_weather_keyboard(weather['city'])
        )
        
    except APITimeoutError:
        await message.answer(
            "⏱ <b>Превышено время ожидания</b>\n\n"
            "Сервис погоды временно недоступен. Попробуйте позже."
        )
    
    except Exception as e:
        logger.error(f"Ошибка получения погоды по координатам: {e}")
        await message.answer(
            "😔 Не удалось определить погоду в вашем местоположении\n"
            "Попробуйте еще раз или отправьте название города"
        )