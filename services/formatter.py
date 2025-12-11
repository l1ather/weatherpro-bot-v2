
from datetime import datetime
from typing import Dict, List


class WeatherFormatter:
    """Форматирование данных о погоде"""
    
    # Расширенные emoji для погодных условий
    WEATHER_EMOJI = {
        '01d': '☀️',  '01n': '🌙',
        '02d': '⛅',  '02n': '☁️',
        '03d': '☁️',  '03n': '☁️',
        '04d': '☁️',  '04n': '☁️',
        '09d': '🌧',  '09n': '🌧',
        '10d': '🌦',  '10n': '🌧',
        '11d': '⛈',  '11n': '⛈',
        '13d': '❄️',  '13n': '❄️',
        '50d': '🌫',  '50n': '🌫',
    }
    
    DAYS_RU = {
        0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
        4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
    }
    
    @classmethod
    def format_current_weather(cls, data: Dict, from_cache: bool = False) -> str:
        """Форматирование текущей погоды"""
        emoji = cls.WEATHER_EMOJI.get(data['icon'], '🌡')
        temp = data['temp']
        
        # Определяем эмодзи температуры
        temp_emoji = cls._get_temp_emoji(temp)
        
        # Определяем уровень комфорта
        comfort = cls._get_comfort_level(data['temp'], data['feels_like'])
        
        text = (
            f"{emoji} <b>Погода в городе {data['city']}, {data['country']}</b>\n\n"
            f"{temp_emoji} Температура: <b>{temp:+d}°C</b>\n"
            f"🤔 Ощущается как: {data['feels_like']:+d}°C {comfort}\n"
            f"📝 {data['description']}\n\n"
            f"💧 Влажность: {data['humidity']}% {cls._get_humidity_status(data['humidity'])}\n"
            f"🌪 Ветер: {data['wind_speed']} м/с {cls._get_wind_status(data['wind_speed'])}\n"
            f"🔽 Давление: {data['pressure']} мм рт.ст.\n"
            f"☁️ Облачность: {data['clouds']}%\n"
        )
        
        # Добавляем рекомендации
        recommendations = cls._get_recommendations(data)
        if recommendations:
            text += f"\n💡 <i>{recommendations}</i>\n"
        
        # Индикатор кеша
        if from_cache:
            text += "\n📦 <i>Данные из кеша</i>"
        
        return text
    
    @classmethod
    def format_forecast(cls, city: str, forecast_data: List[Dict]) -> str:
        """Форматирование прогноза"""
        text = f"📅 <b>Прогноз погоды для города {city}</b>\n\n"
        
        for day in forecast_data:
            date = datetime.strptime(day['date'], '%Y-%m-%d')
            day_name = cls.DAYS_RU[date.weekday()]
            date_str = date.strftime('%d.%m')
            
            emoji = cls.WEATHER_EMOJI.get(day['icon'], '🌡')
            temp_emoji = cls._get_temp_emoji(day['temp'])
            
            text += (
                f"{emoji} <b>{day_name}, {date_str}</b>\n"
                f"   {temp_emoji} {day['temp']:+d}°C "
                f"(↓{day['temp_min']:+d}° ↑{day['temp_max']:+d}°)\n"
                f"   📝 {day['description']}\n"
                f"   💧 {day['humidity']}% | 🌪 {day['wind_speed']} м/с\n\n"
            )
        
        return text
    
    @staticmethod
    def _get_temp_emoji(temp: int) -> str:
        """Эмодзи в зависимости от температуры"""
        if temp <= -20: return "🥶"
        elif temp <= -10: return "❄️"
        elif temp <= 0: return "🧊"
        elif temp <= 10: return "🧥"
        elif temp <= 20: return "🌡"
        elif temp <= 30: return "☀️"
        else: return "🔥"
    
    @staticmethod
    def _get_comfort_level(temp: int, feels_like: int) -> str:
        """Уровень комфорта"""
        diff = abs(temp - feels_like)
        if diff <= 2:
            return "✅"
        elif diff <= 5:
            return "⚠️"
        else:
            return "❌"
    
    @staticmethod
    def _get_humidity_status(humidity: int) -> str:
        """Статус влажности"""
        if humidity < 30:
            return "🏜 Сухо"
        elif humidity < 60:
            return "✅ Комфортно"
        elif humidity < 80:
            return "💦 Влажно"
        else:
            return "☔ Очень влажно"
    
    @staticmethod
    def _get_wind_status(wind_speed: float) -> str:
        """Статус ветра"""
        if wind_speed < 2:
            return "🍃 Тихо"


        elif wind_speed < 5:
            return "🌬 Легкий"
        elif wind_speed < 10:
            return "💨 Умеренный"
        elif wind_speed < 15:
            return "🌪 Сильный"
        else:
            return "⚠️ Очень сильный"
            
    @staticmethod
    def _get_recommendations(data: Dict) -> str:
        """Рекомендации по погоде"""
        temp = data['temp']
        wind = data['wind_speed']
        humidity = data['humidity']
                
        tips = []
                
        if temp < 0:
            tips.append("Тепло одевайтесь!")
        elif temp > 30:
            tips.append("Возьмите воду с собой")
                
        if wind > 10:
            tips.append("Сильный ветер - будьте осторожны")
                
        if humidity > 80:
            tips.append("Высокая влажность - возможен дождь")
                
        if data['icon'] in ['09d', '09n', '10d', '10n']:
            tips.append("Не забудьте зонт! ☔")
                
        return ". ".join(tips)