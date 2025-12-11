import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database.models import init_db
from database.crud import FavoriteCityCRUD, UserCRUD
from keyboards.inline import get_favorites_keyboard, get_city_actions_keyboard

router = Router()
logger = logging.getLogger(__name__)

# Инициализация БД
SessionLocal = init_db()


@router.message(Command("favorites"))
@router.message(F.text == "⭐ Избранное")
async def show_favorites(message: Message):
    """Показать избранные города"""
    session = SessionLocal()
    try:
        user = UserCRUD.get_or_create(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        
        favorites = FavoriteCityCRUD.get_all(session, user.id)
        
        if not favorites:
            await message.answer(
                "⭐ <b>Избранные города</b>\n\n"
                "У вас пока нет избранных городов.\n\n"
                "Чтобы добавить город в избранное, нажмите кнопку ⭐ "
                "при просмотре погоды в этом городе."
            )
            return
        
        text = "⭐ <b>Ваши избранные города:</b>\n\n"
        
        for favorite in favorites:
            city_display = favorite.city_name
            if favorite.country_code:
                city_display += f", {favorite.country_code}"
            text += f"📍 {city_display}\n"
        
        await message.answer(
            text,
            reply_markup=get_favorites_keyboard(favorites)
        )
    
    finally:
        session.close()


@router.callback_query(F.data.startswith("fav_weather:"))
async def show_favorite_weather(callback: CallbackQuery, cache):
    """Показать погоду для избранного города"""
    city = callback.data.split(":", 1)[1]
    
    await callback.answer(f"🔍 Загружаю погоду для {city}...")
    
    # Импортируем здесь, чтобы избежать циклических импортов
    from services.weather_api import WeatherAPI, CityNotFoundError
    from services.formatter import WeatherFormatter
    
    session = SessionLocal()
    try:
        api = WeatherAPI(cache)
        weather = await api.get_current_weather(city)
        
        # Логируем запрос
        from database.crud import WeatherRequestCRUD, UserCRUD
        user = UserCRUD.get_or_create(session, callback.from_user.id)
        WeatherRequestCRUD.create(session, user.id, city, 'current', success=True)
        
        text = WeatherFormatter.format_current_weather(weather)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_city_actions_keyboard(city, is_favorite=True)
        )
    
    except CityNotFoundError:
        await callback.answer("❌ Город не найден", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка получения погоды для избранного: {e}")
        await callback.answer("❌ Ошибка загрузки", show_alert=True)
    
    finally:
        session.close()


@router.callback_query(F.data.startswith("add_favorite:"))
async def add_to_favorites(callback: CallbackQuery):
    """Добавить город в избранное"""
    city = callback.data.split(":", 1)[1]
    
    session = SessionLocal()
    try:
        user = UserCRUD.get_or_create(session, callback.from_user.id)
        
        # Проверяем лимит (максимум 10 городов)
        favorites = FavoriteCityCRUD.get_all(session, user.id)
        
        if len(favorites) >= 10:
            await callback.answer(
                "❌ Достигнут лимит избранных городов (10).\n"
                "Удалите ненужные города перед добавлением новых.",
                show_alert=True
            )
            return
        
        # Добавляем город
        FavoriteCityCRUD.add(session, user.id, city)
        
        await callback.answer(f"⭐ Город {city} добавлен в избранное!", show_alert=False)
        
        # Обновляем клавиатуру
        await callback.message.edit_reply_markup(

reply_markup=get_city_actions_keyboard(city, is_favorite=True)
        )
    
    finally:
        session.close()


@router.callback_query(F.data.startswith("remove_favorite:"))
async def remove_from_favorites(callback: CallbackQuery):
    """Удалить город из избранного"""
    city = callback.data.split(":", 1)[1]
    
    session = SessionLocal()
    try:
        user = UserCRUD.get_or_create(session, callback.from_user.id)
        
        success = FavoriteCityCRUD.remove(session, user.id, city)
        
        if success:
            await callback.answer(f"🗑 Город {city} удален из избранного", show_alert=False)
            
            # Обновляем клавиатуру
            await callback.message.edit_reply_markup(
                reply_markup=get_city_actions_keyboard(city, is_favorite=False)
            )
        else:
            await callback.answer("❌ Город не найден в избранном", show_alert=True)
    
    finally:
        session.close()


@router.message(Command("stats"))
async def show_stats(message: Message):
    """Показать статистику пользователя (только для админов)"""
    # Проверяем, является ли пользователь админом
    # В реальном приложении здесь будет проверка ID
    admin_ids = [123456789]  # Замените на реальные ID админов
    
    if message.from_user.id not in admin_ids:
        await message.answer("⛔ Недостаточно прав")
        return
    
    session = SessionLocal()
    try:
        from database.crud import WeatherRequestCRUD, UserCRUD
        
        stats = WeatherRequestCRUD.get_stats(session, days=7)
        active_users = UserCRUD.get_active_users_count(session, days=7)
        popular_cities = WeatherRequestCRUD.get_popular_cities(session, days=7, limit=5)
        
        text = (
            "📊 <b>Статистика за последние 7 дней:</b>\n\n"
            f"👥 Активных пользователей: {active_users}\n"
            f"📝 Всего запросов: {stats['total']}\n"
            f"✅ Успешных: {stats['successful']}\n"
            f"❌ Ошибок: {stats['failed']}\n"
            f"📈 Success rate: {stats['success_rate']:.1f}%\n\n"
            "<b>🏆 Популярные города:</b>\n"
        )
        
        for i, (city, count) in enumerate(popular_cities, 1):
            text += f"{i}. {city} — {count} запросов\n"
        
        await message.answer(text)
    
    finally:
        session.close()