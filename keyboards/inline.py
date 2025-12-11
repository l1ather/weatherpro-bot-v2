from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_city_actions_keyboard(city: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура действий с городом"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📅 Прогноз на 5 дней",
                callback_data=f"forecast:{city}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"current:{city}"
            )
        ]
    ]
    
    # Кнопка избранного
    if is_favorite:
        keyboard.append([
            InlineKeyboardButton(
                text="🗑 Удалить из избранного",
                callback_data=f"remove_favorite:{city}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="⭐ Добавить в избранное",
                callback_data=f"add_favorite:{city}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_favorites_keyboard(favorites: List) -> InlineKeyboardMarkup:
    """Клавиатура со списком избранных городов"""
    keyboard = []
    
    for favorite in favorites:
        city_display = favorite.city_name
        if favorite.country_code:
            city_display += f", {favorite.country_code}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"🌤 {city_display}",
                callback_data=f"fav_weather:{favorite.city_name}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"remove_favorite:{favorite.city_name}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_forecast_keyboard(city: str, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для прогноза погоды"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🌤 Текущая погода",
                callback_data=f"current:{city}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Обновить прогноз",
                callback_data=f"forecast:{city}"
            )
        ]
    ]
    
    # Кнопка избранного
    if is_favorite:
        keyboard.append([
            InlineKeyboardButton(
                text="🗑 Удалить из избранного",
                callback_data=f"remove_favorite:{city}"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                text="⭐ Добавить в избранное",
                callback_data=f"add_favorite:{city}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🌡 Единицы температуры",
                callback_data="settings:temperature"
            )
        ],
        [
            InlineKeyboardButton(
                text="💨 Единицы скорости ветра",
                callback_data="settings:wind"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="settings:notifications"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏙 Город по умолчанию",
                callback_data="settings:default_city"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_temperature_units_keyboard() -> InlineKeyboardMarkup:
    """Выбор единиц температуры"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="°C Цельсий",
                callback_data="unit:temp:celsius"
            )
        ],
        [
            InlineKeyboardButton(
                text="°F Фаренгейт",
                callback_data="unit:temp:fahrenheit"
            )
        ],
        [
            InlineKeyboardButton(
                text="« Назад",

callback_data="settings:back"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Да",
                callback_data=f"confirm:{action}:{data}"
            ),
            InlineKeyboardButton(
                text="❌ Нет",
                callback_data="cancel"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)