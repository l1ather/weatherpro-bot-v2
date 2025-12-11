import re
from typing import Optional


class CityValidator:
    """Валидатор для названий городов"""
    
    # Разрешенные символы: буквы, пробелы, дефисы, апострофы
    CITY_PATTERN = re.compile(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$")
    
    # Максимальная длина названия города
    MAX_LENGTH = 100
    
    # Минимальная длина названия города
    MIN_LENGTH = 2
    
    @classmethod
    def is_valid(cls, city_name: str) -> bool:
        """Проверить валидность названия города"""
        if not city_name:
            return False
        
        city_name = city_name.strip()
        
        # Проверка длины
        if len(city_name) < cls.MIN_LENGTH or len(city_name) > cls.MAX_LENGTH:
            return False
        
        # Проверка паттерна
        if not cls.CITY_PATTERN.match(city_name):
            return False
        
        return True
    
    @classmethod
    def sanitize(cls, city_name: str) -> Optional[str]:
        """Очистить и нормализовать название города"""
        if not city_name:
            return None
        
        # Убираем лишние пробелы
        city_name = ' '.join(city_name.strip().split())
        
        # Проверяем валидность
        if not cls.is_valid(city_name):
            return None
        
        # Первая буква каждого слова заглавная
        city_name = city_name.title()
        
        return city_name
    
    @classmethod
    def get_error_message(cls, city_name: str) -> str:
        """Получить сообщение об ошибке"""
        if not city_name:
            return "Название города не может быть пустым"
        
        city_name = city_name.strip()
        
        if len(city_name) < cls.MIN_LENGTH:
            return f"Название города слишком короткое (минимум {cls.MIN_LENGTH} символа)"
        
        if len(city_name) > cls.MAX_LENGTH:
            return f"Название города слишком длинное (максимум {cls.MAX_LENGTH} символов)"
        
        if not cls.CITY_PATTERN.match(city_name):
            return "Название города содержит недопустимые символы"
        
        return "Неверное название города"


class CoordinatesValidator:
    """Валидатор для координат"""
    
    @staticmethod
    def is_valid_latitude(lat: float) -> bool:
        """Проверить валидность широты"""
        return -90 <= lat <= 90
    
    @staticmethod
    def is_valid_longitude(lon: float) -> bool:
        """Проверить валидность долготы"""
        return -180 <= lon <= 180
    
    @classmethod
    def is_valid(cls, lat: float, lon: float) -> bool:
        """Проверить валидность координат"""
        return cls.is_valid_latitude(lat) and cls.is_valid_longitude(lon)


class UserInputSanitizer:
    """Санитизация пользовательского ввода"""
    
    # Запрещенные символы
    FORBIDDEN_CHARS = ['<', '>', '&', '"', "'", '/', '\\', ';']
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: int = 1000) -> str:
        """Очистить текст от потенциально опасных символов"""
        if not text:
            return ""
        
        # Обрезаем до максимальной длины
        text = text[:max_length]
        
        # Убираем запрещенные символы
        for char in cls.FORBIDDEN_CHARS:
            text = text.replace(char, '')
        
        # Убираем множественные пробелы
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def is_command(text: str) -> bool:
        """Проверить, является ли текст командой"""
        return text.startswith('/') if text else False
    
    @staticmethod
    def extract_command(text: str) -> tuple[str, str]:
        """Извлечь команду и аргументы"""
        if not text or not text.startswith('/'):
            return "", ""
        
        parts = text.split(maxsplit=1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        return command, args


class RateLimiter:
    """Ограничение частоты запросов"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        :param max_requests: максимальное количество запросов

l1ather, [11.12.2025 22:07]
:param time_window: временное окно в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, user_id: int) -> tuple[bool, int]:
        """
        Проверить, разрешен ли запрос
        
        :return: (разрешен, секунд до следующей попытки)
        """
        import time
        
        current_time = time.time()
        
        # Очищаем старые записи
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if current_time - req_time < self.time_window
            ]
        
        # Проверяем лимит
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        if len(self.requests[user_id]) >= self.max_requests:
            oldest_request = min(self.requests[user_id])
            wait_time = int(self.time_window - (current_time - oldest_request))
            return False, wait_time
        
        # Добавляем текущий запрос
        self.requests[user_id].append(current_time)
        
        return True, 0


# Примеры использования
if __name__ == "__main__":
    # Тест валидатора городов
    print("City Validator Tests:")
    print(CityValidator.is_valid("Moscow"))  # True
    print(CityValidator.is_valid("New York"))  # True
    print(CityValidator.is_valid("Saint-Petersburg"))  # True
    print(CityValidator.is_valid("Москва"))  # True
    print(CityValidator.is_valid("123"))  # False
    print(CityValidator.is_valid("City<script>"))  # False
    
    print("\nSanitized cities:")
    print(CityValidator.sanitize("  moscow  "))  # Moscow
    print(CityValidator.sanitize("new   york"))  # New York
    print(CityValidator.sanitize("LONDON"))  # London