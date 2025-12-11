import logging
from typing import Optional
import aiohttp
from config import settings
from .cache import RedisCache

logger = logging.getLogger(__name__)


class WeatherAPIError(Exception):
    """Базовое исключение для API"""
    pass


class CityNotFoundError(WeatherAPIError):
    """Город не найден"""
    pass


class APITimeoutError(WeatherAPIError):
    """Таймаут запроса"""
    pass


class WeatherAPI:
    """Сервис работы с OpenWeather API"""
    
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.api_key = settings.OPENWEATHER_API_KEY
    
    async def _make_request(self, endpoint: str, params: dict) -> dict:
        """Базовый метод для запросов к API"""
        params['appid'] = self.api_key
        params['units'] = 'metric'
        params['lang'] = 'ru'
        
        url = f"{self.base_url}/{endpoint}"
        
        timeout = aiohttp.ClientTimeout(total=settings.API_TIMEOUT)
        
        for attempt in range(settings.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 404:
                            raise CityNotFoundError("Город не найден")
                        
                        if response.status != 200:
                            raise WeatherAPIError(f"API вернул код {response.status}")
                        
                        return await response.json()
            
            except aiohttp.ClientError as e:
                if attempt == settings.MAX_RETRIES - 1:
                    logger.error(f"❌ Ошибка API после {settings.MAX_RETRIES} попыток: {e}")
                    raise APITimeoutError("Не удалось получить данные")
                logger.warning(f"⚠️ Попытка {attempt + 1} не удалась, повтор...")
    
    async def get_current_weather(self, city: str) -> dict:
        """Получить текущую погоду по названию города"""
        cache_key = self.cache.make_key('weather', city)
        
        # Проверяем кеш
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Запрос к API
        data = await self._make_request('weather', {'q': city})
        
        # Форматируем данные
        weather_data = self._format_current_weather(data)
        
        # Кешируем
        await self.cache.set(cache_key, weather_data, settings.CACHE_TTL)
        
        return weather_data
    
    async def get_weather_by_coords(self, lat: float, lon: float) -> dict:
        """Получить погоду по координатам"""
        cache_key = self.cache.make_key('weather_coords', f"{lat:.2f}", f"{lon:.2f}")
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        data = await self._make_request('weather', {'lat': lat, 'lon': lon})
        weather_data = self._format_current_weather(data)
        
        await self.cache.set(cache_key, weather_data, settings.CACHE_TTL)
        
        return weather_data
    
    async def get_forecast(self, city: str) -> list[dict]:
        """Получить прогноз на 5 дней"""
        cache_key = self.cache.make_key('forecast', city)
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        data = await self._make_request('forecast', {'q': city})
        forecast_data = self._format_forecast(data)
        
        await self.cache.set(cache_key, forecast_data, settings.FORECAST_CACHE_TTL)
        
        return forecast_data
    
    def _format_current_weather(self, data: dict) -> dict:
        """Форматирование данных текущей погоды"""
        return {
            'city': data['name'],
            'country': data['sys']['country'],
            'temp': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'description': data['weather'][0]['description'].capitalize(),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'clouds': data['clouds']['all'],
            'icon': data['weather'][0]['icon']
        }
    
    def _format_forecast(self, data: dict) -> list[dict]:
        """Форматирование прогноза погоды"""
        forecasts = []
        
        # Берем прогноз на полдень каждого дня
        daily_forecasts = {}
        
        for item in data['list']:
            date = item['dt_txt'].split()[0]
            hour = item['dt_txt'].split()[1]
            
            # Берем прогноз на 12:00
            if hour == '12:00:00' and date not in daily_forecasts:
                daily_forecasts[date] = {
                    'date': date,
                    'temp': round(item['main']['temp']),
                    'temp_min': round(item['main']['temp_min']),
                    'temp_max': round(item['main']['temp_max']),
                    'description': item['weather'][0]['description'].capitalize(),
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed'],
                    'icon': item['weather'][0]['icon']
                }
        
        return list(daily_forecasts.values())[:5]