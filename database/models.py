from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default='ru')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.telegram_id}>"


class FavoriteCity(Base):
    """Избранные города пользователя"""
    __tablename__ = 'favorite_cities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    city_name = Column(String(255), nullable=False)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FavoriteCity {self.city_name} for user {self.user_id}>"


class WeatherRequest(Base):
    """История запросов погоды"""
    __tablename__ = 'weather_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    city_name = Column(String(255), nullable=False)
    request_type = Column(String(50), nullable=False)  # current, forecast, location
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<WeatherRequest {self.city_name} by {self.user_id}>"


class UserSettings(Base):
    """Настройки пользователя"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    temperature_unit = Column(String(10), default='celsius')  # celsius, fahrenheit
    wind_unit = Column(String(10), default='ms')  # ms, kmh, mph
    notifications_enabled = Column(Boolean, default=False)
    default_city = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSettings for user {self.user_id}>"


# Database connection
def init_db(database_url: str = "sqlite:///weather_bot.db"):
    """Инициализация базы данных"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal


# Пример использования
if __name__ == "__main__":
    SessionLocal = init_db()
    session = SessionLocal()
    
    # Создание тестового пользователя
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    session.add(user)
    session.commit()
    
    print("✅ База данных инициализирована")
    session.close()