from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Настройки приложения WeatherPro Bot v2"""
    
    # ===== Telegram =====
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота")
    
    # ===== OpenWeather API =====
    OPENWEATHER_API_KEY: str = Field(..., description="API ключ OpenWeather")
    OPENWEATHER_BASE_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="Базовый URL OpenWeather API"
    )
    
    # ===== Redis =====
    REDIS_HOST: str = Field(default="localhost", description="Хост Redis")
    REDIS_PORT: int = Field(default=6379, description="Порт Redis")
    REDIS_DB: int = Field(default=0, description="Номер БД Redis")
    REDIS_PASSWORD: str | None = Field(default=None, description="Пароль Redis")
    
    # ===== Cache Settings =====
    CACHE_TTL: int = Field(default=3600, description="TTL кеша текущей погоды (секунды)")
    FORECAST_CACHE_TTL: int = Field(default=7200, description="TTL кеша прогноза (секунды)")
    
    # ===== API Settings =====
    API_TIMEOUT: int = Field(default=10, description="Таймаут API запросов (секунды)")
    MAX_RETRIES: int = Field(default=3, description="Максимум попыток повтора")
    
    # ===== Database =====
    DATABASE_URL: str = Field(
        default="sqlite:///weather_bot.db",
        description="URL подключения к БД"
    )
    DB_POOL_SIZE: int = Field(default=5, description="Размер пула соединений")
    DB_TIMEOUT: int = Field(default=30, description="Таймаут операций с БД")
    
    # ===== Application Settings =====
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    MAX_FAVORITE_CITIES: int = Field(default=10, description="Максимум избранных городов")
    
    # ===== Admin Settings =====
    ADMIN_IDS: List[int] = Field(default_factory=list, description="ID администраторов")
    
    @validator('ADMIN_IDS', pre=True)
    def parse_admin_ids(cls, v):
        """Парсинг списка ID админов из строки"""
        if isinstance(v, str):
            if not v:
                return []
            return [int(id_) for id_ in v.split(',') if id_.strip()]
        return v
    
    # ===== Rate Limiting =====
    RATE_LIMIT: float = Field(default=1.0, description="Минимум секунд между запросами")
    MAX_REQUESTS_PER_WINDOW: int = Field(default=10, description="Макс запросов в окне")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Окно для rate limit (секунды)")
    
    # ===== Feature Flags =====
    ENABLE_FAVORITES: bool = Field(default=True, description="Включить избранное")
    ENABLE_STATISTICS: bool = Field(default=True, description="Включить статистику")
    ENABLE_NOTIFICATIONS: bool = Field(default=False, description="Включить уведомления")
    
    # ===== Logging =====
    LOG_FILE: str = Field(default="logs/bot.log", description="Путь к файлу логов")
    LOG_MAX_SIZE: int = Field(default=10, description="Макс размер лога (MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Количество файлов логов")
    
    # ===== Development =====
    DEBUG: bool = Field(default=False, description="Режим отладки")
    TEST_MODE: bool = Field(default=False, description="Тестовый режим")
    
    # ===== Localization =====
    DEFAULT_LANGUAGE: str = Field(default="ru", description="Язык по умолчанию")
    SUPPORTED_LANGUAGES: List[str] = Field(
        default_factory=lambda: ["ru", "en"],
        description="Поддерживаемые языки"
    )
    
    @validator('SUPPORTED_LANGUAGES', pre=True)
    def parse_languages(cls, v):
        """Парсинг списка языков из строки"""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(',') if lang.strip()]
        return v
    
    # ===== Notifications =====
    NOTIFICATION_TIME: str = Field(default="08:00", description="Время уведомлений")
    NOTIFICATION_TIMEZONE: str = Field(default="Europe/Moscow", description="Часовой пояс")
    
    # ===== External Services =====

    SENTRY_DSN: str | None = Field(default=None, description="Sentry DSN для мониторинга")
    METRICS_ENABLED: bool = Field(default=False, description="Включить Prometheus метрики")
    METRICS_PORT: int = Field(default=9090, description="Порт для метрик")
    
    # ===== Security =====
    SECRET_KEY: str | None = Field(default=None, description="Секретный ключ")
    ALLOWED_DOMAINS: List[str] = Field(
        default_factory=list,
        description="Разрешенные домены"
    )
    
    @validator('ALLOWED_DOMAINS', pre=True)
    def parse_domains(cls, v):
        """Парсинг списка доменов из строки"""
        if isinstance(v, str):
            if not v:
                return []
            return [domain.strip() for domain in v.split(',') if domain.strip()]
        return v
    
    # ===== Pydantic Config =====
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # ===== Validation Methods =====
    @validator('CACHE_TTL', 'FORECAST_CACHE_TTL')
    def validate_ttl(cls, v):
        """Проверка TTL"""
        if v < 60:
            raise ValueError("TTL должен быть не менее 60 секунд")
        return v
    
    @validator('MAX_RETRIES')
    def validate_retries(cls, v):
        """Проверка количества попыток"""
        if v < 1 or v > 10:
            raise ValueError("MAX_RETRIES должен быть от 1 до 10")
        return v
    
    @validator('RATE_LIMIT')
    def validate_rate_limit(cls, v):
        """Проверка rate limit"""
        if v < 0.1 or v > 60:
            raise ValueError("RATE_LIMIT должен быть от 0.1 до 60 секунд")
        return v
    
    # ===== Helper Methods =====
    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь админом"""
        return user_id in self.ADMIN_IDS
    
    def get_redis_url(self) -> str:
        """Получить URL для подключения к Redis"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def get_log_format(self) -> str:
        """Получить формат логирования"""
        if self.DEBUG:
            return "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Глобальный инстанс настроек
settings = Settings()


# Вспомогательные функции
def get_settings() -> Settings:
    """Получить инстанс настроек"""
    return settings


def reload_settings() -> Settings:
    """Перезагрузить настройки"""
    global settings
    settings = Settings()
    return settings


# Валидация при импорте
if __name__ == "__main__":
    print("🔍 Проверка конфигурации...")
    
    try:
        s = Settings()
        print("✅ Конфигурация валидна!")
        print(f"\n📊 Настройки:")
        print(f"  - Bot Token: {'*' * 10}{s.BOT_TOKEN[-5:]}")
        print(f"  - Redis: {s.REDIS_HOST}:{s.REDIS_PORT}")
        print(f"  - Database: {s.DATABASE_URL}")
        print(f"  - Cache TTL: {s.CACHE_TTL}s")
        print(f"  - Admin IDs: {s.ADMIN_IDS}")
        print(f"  - Debug Mode: {s.DEBUG}")
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        exit(1)