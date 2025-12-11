
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from .models import User, FavoriteCity, WeatherRequest, UserSettings


class UserCRUD:
    """CRUD операции для пользователей"""
    
    @staticmethod
    def get_or_create(session: Session, telegram_id: int, **kwargs) -> User:
        """Получить или создать пользователя"""
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            user = User(telegram_id=telegram_id, **kwargs)
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Обновляем последнюю активность
            user.last_activity = datetime.utcnow()
            session.commit()
        
        return user
    
    @staticmethod
    def get_active_users_count(session: Session, days: int = 7) -> int:
        """Количество активных пользователей за период"""
        threshold = datetime.utcnow() - timedelta(days=days)
        return session.query(User).filter(
            User.last_activity >= threshold
        ).count()
    
    @staticmethod
    def update(session: Session, telegram_id: int, **kwargs) -> Optional[User]:
        """Обновить данные пользователя"""
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            session.commit()
            session.refresh(user)
        return user


class FavoriteCityCRUD:
    """CRUD операции для избранных городов"""
    
    @staticmethod
    def add(session: Session, user_id: int, city_name: str, country_code: str = None) -> FavoriteCity:
        """Добавить город в избранное"""
        # Проверяем, нет ли уже такого города
        existing = session.query(FavoriteCity).filter_by(
            user_id=user_id,
            city_name=city_name
        ).first()
        
        if existing:
            return existing
        
        favorite = FavoriteCity(
            user_id=user_id,
            city_name=city_name,
            country_code=country_code
        )
        session.add(favorite)
        session.commit()
        session.refresh(favorite)
        return favorite
    
    @staticmethod
    def get_all(session: Session, user_id: int) -> List[FavoriteCity]:
        """Получить все избранные города пользователя"""
        return session.query(FavoriteCity).filter_by(
            user_id=user_id
        ).order_by(FavoriteCity.created_at.desc()).all()
    
    @staticmethod
    def remove(session: Session, user_id: int, city_name: str) -> bool:
        """Удалить город из избранного"""
        favorite = session.query(FavoriteCity).filter_by(
            user_id=user_id,
            city_name=city_name
        ).first()
        
        if favorite:
            session.delete(favorite)
            session.commit()
            return True
        return False
    
    @staticmethod
    def is_favorite(session: Session, user_id: int, city_name: str) -> bool:
        """Проверить, в избранном ли город"""
        return session.query(FavoriteCity).filter_by(
            user_id=user_id,
            city_name=city_name
        ).first() is not None


class WeatherRequestCRUD:
    """CRUD операции для запросов погоды"""
    
    @staticmethod
    def create(session: Session, user_id: int, city_name: str, 
               request_type: str, success: bool = True) -> WeatherRequest:
        """Создать запись о запросе"""
        request = WeatherRequest(
            user_id=user_id,
            city_name=city_name,
            request_type=request_type,
            success=success
        )
        session.add(request)
        session.commit()
        return request
    
    @staticmethod
    def get_user_history(session: Session, user_id: int, limit: int = 10) -> List[WeatherRequest]:
        """Получить историю запросов пользователя"""
        return session.query(WeatherRequest).filter_by(
            user_id=user_id
        ).order_by(WeatherRequest.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_popular_cities(session: Session, days: int = 30, limit: int = 10) -> List[tuple]:
        """Получить популярные города"""
        threshold = datetime.utcnow() - timedelta(days=days)
        
        from sqlalchemy import func
        
        return session.query(
            WeatherRequest.city_name,
            func.count(WeatherRequest.id).label('count')
        ).filter(
            WeatherRequest.created_at >= threshold,
            WeatherRequest.success == True
        ).group_by(
            WeatherRequest.city_name
        ).order_by(
            func.count(WeatherRequest.id).desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_stats(session: Session, days: int = 7) -> dict:
        """Получить статистику запросов"""
        threshold = datetime.utcnow() - timedelta(days=days)
        
        from sqlalchemy import func
        
        total = session.query(func.count(WeatherRequest.id)).filter(
            WeatherRequest.created_at >= threshold
        ).scalar()
        
        successful = session.query(func.count(WeatherRequest.id)).filter(
            WeatherRequest.created_at >= threshold,
            WeatherRequest.success == True
        ).scalar()
        
        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }


class UserSettingsCRUD:
    """CRUD операции для настроек пользователей"""
    
    @staticmethod
    def get_or_create(session: Session, user_id: int) -> UserSettings:
        """Получить или создать настройки"""
        settings = session.query(UserSettings).filter_by(user_id=user_id).first()
        
        if not settings:
            settings = UserSettings(user_id=user_id)
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        return settings
    
    @staticmethod
    def update(session: Session, user_id: int, **kwargs) -> Optional[UserSettings]:
        """Обновить настройки"""
        settings = session.query(UserSettings).filter_by(user_id=user_id).first()
        
        if settings:
            for key, value in kwargs.items():
                setattr(settings, key, value)
            settings.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(settings)
        
        return settings