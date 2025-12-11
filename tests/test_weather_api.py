import pytest
from unittest.mock import AsyncMock, MagicMock
from services.weather_api import WeatherAPI, CityNotFoundError, APITimeoutError
from services.cache import RedisCache


class TestWeatherAPI:
    """Тесты для WeatherAPI"""
    
    @pytest.fixture
    def mock_cache(self):
        """Мок Redis кеша"""
        cache = MagicMock(spec=RedisCache)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.make_key = MagicMock(return_value="test_key")
        return cache
    
    @pytest.fixture
    def weather_api(self, mock_cache):
        """Инстанс WeatherAPI с моком кеша"""
        return WeatherAPI(mock_cache)
    
    @pytest.mark.asyncio
    async def test_get_current_weather_success(self, weather_api, mock_cache, aioresponses):
        """Тест успешного получения погоды"""
        # Подготовка мок ответа от API
        mock_response = {
            'name': 'Moscow',
            'sys': {'country': 'RU'},
            'main': {
                'temp': 20.5,
                'feels_like': 19.0,
                'humidity': 65,
                'pressure': 1013
            },
            'weather': [{
                'description': 'clear sky',
                'icon': '01d'
            }],
            'wind': {'speed': 3.5},
            'clouds': {'all': 10}
        }
        
        aioresponses.get(
            'https://api.openweathermap.org/data/2.5/weather',
            payload=mock_response
        )
        
        # Выполнение
        result = await weather_api.get_current_weather('Moscow')
        
        # Проверки
        assert result['city'] == 'Moscow'
        assert result['country'] == 'RU'
        assert result['temp'] == 21  # Округлено
        assert result['feels_like'] == 19
        assert result['description'] == 'Clear sky'
        
        # Проверяем, что данные были закешированы
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_weather_from_cache(self, weather_api, mock_cache):
        """Тест получения погоды из кеша"""
        # Подготовка данных в кеше
        cached_data = {
            'city': 'London',
            'country': 'UK',
            'temp': 15,
            'feels_like': 14,
            'description': 'Cloudy',
            'humidity': 70,
            'pressure': 1010,
            'wind_speed': 4.0,
            'clouds': 80,
            'icon': '03d'
        }
        mock_cache.get = AsyncMock(return_value=cached_data)
        
        # Выполнение
        result = await weather_api.get_current_weather('London')
        
        # Проверки
        assert result == cached_data
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()  # Не должны писать в кеш
    
    @pytest.mark.asyncio
    async def test_get_current_weather_city_not_found(self, weather_api, aioresponses):
        """Тест обработки ошибки 'город не найден'"""
        aioresponses.get(
            'https://api.openweathermap.org/data/2.5/weather',
            status=404
        )
        
        with pytest.raises(CityNotFoundError):
            await weather_api.get_current_weather('NonExistentCity123')
    
    @pytest.mark.asyncio
    async def test_get_current_weather_timeout(self, weather_api, aioresponses):
        """Тест обработки таймаута"""
        import aiohttp
        
        aioresponses.get(
            'https://api.openweathermap.org/data/2.5/weather',
            exception=aiohttp.ClientError("Timeout")
        )
        
        with pytest.raises(APITimeoutError):
            await weather_api.get_current_weather('Moscow')
    
    @pytest.mark.asyncio
    async def test_get_weather_by_coords(self, weather_api, mock_cache, aioresponses):
        """Тест получения погоды по координатам"""
        mock_response = {
            'name': 'New York',
            'sys': {'country': 'US'},
            'main': {
                'temp': 25.0,
                'feels_like': 26.0,
                'humidity': 55,
                'pressure': 1015
            },
'weather': [{
                'description': 'sunny',
                'icon': '01d'
            }],
            'wind': {'speed': 2.5},
            'clouds': {'all': 5}
        }
        
        aioresponses.get(
            'https://api.openweathermap.org/data/2.5/weather',
            payload=mock_response
        )
        
        result = await weather_api.get_weather_by_coords(40.7128, -74.0060)
        
        assert result['city'] == 'New York'
        assert result['country'] == 'US'


class TestCityValidator:
    """Тесты для валидатора городов"""
    
    def test_valid_cities(self):
        """Тест валидных названий городов"""
        from utils.validators import CityValidator
        
        assert CityValidator.is_valid("Moscow") == True
        assert CityValidator.is_valid("New York") == True
        assert CityValidator.is_valid("Saint-Petersburg") == True
        assert CityValidator.is_valid("Москва") == True
    
    def test_invalid_cities(self):
        """Тест невалидных названий городов"""
        from utils.validators import CityValidator
        
        assert CityValidator.is_valid("") == False
        assert CityValidator.is_valid("A") == False  # Слишком короткое
        assert CityValidator.is_valid("City123") == False  # Цифры
        assert CityValidator.is_valid("City<script>") == False  # Опасные символы
        assert CityValidator.is_valid("A" * 101) == False  # Слишком длинное
    
    def test_sanitize_city(self):
        """Тест санитизации названий городов"""
        from utils.validators import CityValidator
        
        assert CityValidator.sanitize("  moscow  ") == "Moscow"
        assert CityValidator.sanitize("new   york") == "New York"
        assert CityValidator.sanitize("LONDON") == "London"
        assert CityValidator.sanitize("invalid123") == None


class TestRedisCache:
    """Тесты для Redis кеша"""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, redis_cache):
        """Тест сохранения и получения из кеша"""
        test_data = {'city': 'Moscow', 'temp': 20}
        
        await redis_cache.set('test_key', test_data, ttl=60)
        result = await redis_cache.get('test_key')
        
        assert result == test_data
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, redis_cache):
        """Тест промаха кеша"""
        result = await redis_cache.get('non_existent_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, redis_cache):
        """Тест истечения срока кеша"""
        import asyncio
        
        await redis_cache.set('temp_key', {'data': 'value'}, ttl=1)
        
        # Проверяем сразу
        result = await redis_cache.get('temp_key')
        assert result is not None
        
        # Ждем истечения TTL
        await asyncio.sleep(2)
        
        # Проверяем после истечения
        result = await redis_cache.get('temp_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_make_key(self, redis_cache):
        """Тест генерации ключей"""
        key = redis_cache.make_key('weather', 'Moscow')
        assert key == 'weather:moscow'
        
        key = redis_cache.make_key('forecast', 'New York', '5day')
        assert key == 'forecast:new york:5day'


# Fixtures для pytest
@pytest.fixture
def redis_cache():
    """Фикстура Redis кеша для тестов"""
    # Используем мок или тестовую БД Redis
    cache = MagicMock(spec=RedisCache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.make_key = lambda prefix, *args: f"{prefix}:{':'.join(str(arg).lower() for arg in args)}"
    return cache


@pytest.fixture
def aioresponses():
    """Фикстура для мокирования aiohttp запросов"""
    from aioresponses import aioresponses
    with aioresponses() as m:
        yield m