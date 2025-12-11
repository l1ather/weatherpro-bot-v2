from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = [
        [
            KeyboardButton(text="🌤 Погода сейчас"),
            KeyboardButton(text="📅 Прогноз на 5 дней")
        ],
        [
            KeyboardButton(text="📍 Отправить геолокацию", request_location=True)
        ],
        [
            KeyboardButton(text="ℹ️ Помощь")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или введите название города"
    )


def get_forecast_keyboard(city: str) -> InlineKeyboardMarkup:
    """Клавиатура для прогноза"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔄 Обновить прогноз",
                callback_data=f"forecast:{city}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌤 Текущая погода",
                callback_data=f"current:{city}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_weather_keyboard(city: str) -> InlineKeyboardMarkup:
    """Клавиатура для текущей погоды"""
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
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)