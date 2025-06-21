import re
from typing import Dict, Any, Optional
from datetime import datetime

def format_event_announcement(event: Dict[str, Any]) -> str:
    """Форматирование анонса события для публикации"""
    lines = []
    
    # Заголовок с эмодзи
    if event.get('theme'):
        lines.append(f"🎉 <b>{event['theme']}</b>")
        lines.append("")
    
    # Место проведения
    if event.get('place'):
        formatted_place = format_place_with_link(event['place'])
        lines.append(f"📍 <b>Место:</b> {formatted_place}")
    
    # Время проведения
    if event.get('event_time'):
        lines.append(f"🕐 <b>Время:</b> {event['event_time']}")
    
    # Контакт для связи
    if event.get('contact'):
        lines.append(f"📞 <b>Контакт:</b> {event['contact']}")
    
    # Описание
    if event.get('description'):
        lines.append("")
        lines.append(f"📝 <b>Описание:</b>")
        lines.append(event['description'])
    
    # Призыв к действию
    lines.append("")
    lines.append("👥 Присоединяйтесь к нам!")
    lines.append("#пошли_гулять #событие")
    
    return "\n".join(lines)

def format_admin_preview(event: Dict[str, Any], user_info: str = "") -> str:
    """Форматирование превью для администратора"""
    lines = [
        "🔔 <b>НОВЫЙ АНОНС НА МОДЕРАЦИЮ</b>",
        "",
        f"👤 <b>Автор:</b> {user_info}",
        f"🆔 <b>ID события:</b> {event['id']}",
        "",
        "📋 <b>СОДЕРЖАНИЕ АНОНСА:</b>",
        "=" * 30
    ]
    
    lines.append(format_event_announcement(event))
    
    lines.extend([
        "",
        "=" * 30,
        "⚡ Выберите действие:"
    ])
    
    return "\n".join(lines)

def validate_theme(theme: str) -> bool:
    """Валидация темы события"""
    if not theme or len(theme.strip()) < 3:
        return False
    if len(theme) > 100:
        return False
    return True

def is_google_maps_link(text: str) -> bool:
    """Проверка, является ли текст ссылкой на Google Maps"""
    google_maps_patterns = [
        r'https?://maps\.google\.com/',
        r'https?://www\.google\.com/maps/',
        r'https?://goo\.gl/maps/',
        r'https?://maps\.app\.goo\.gl/',
        r'https?://www\.google\.ru/maps/',
        r'https?://maps\.google\.ru/',
    ]
    
    for pattern in google_maps_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def format_place_with_link(place_text: str) -> str:
    """Форматирование места с поддержкой ссылок"""
    # Проверяем, есть ли в тексте и адрес, и ссылка
    lines = place_text.split('\n')
    
    # Ищем ссылку в тексте
    link = None
    address_parts = []
    
    for line in lines:
        line = line.strip()
        if is_google_maps_link(line):
            link = line
        elif line:
            address_parts.append(line)
    
    # Если есть и адрес, и ссылка
    if link and address_parts:
        address = ' '.join(address_parts)
        return f"{address} — <a href='{link}'>Открыть на карте</a>"
    
    # Если только ссылка
    elif link:
        return f"<a href='{link}'>Открыть на карте</a>"
    
    # Если только текст
    else:
        return place_text

def validate_place(place: str) -> bool:
    """Валидация места события"""
    if not place or len(place.strip()) < 3:
        return False
    if len(place) > 500:  # Увеличиваем лимит для ссылок
        return False
    return True

def validate_contact(contact: str) -> bool:
    """Валидация контакта для связи"""
    if not contact or len(contact.strip()) < 3:
        return False
    if len(contact) > 100:
        return False
    return True

def validate_time(time_str: str) -> bool:
    """Валидация времени события"""
    if not time_str or len(time_str.strip()) < 3:
        return False
    if len(time_str) > 100:
        return False
    # Можно добавить более сложную валидацию времени
    return True

def validate_description(description: str) -> bool:
    """Валидация описания события"""
    if not description:
        return True  # Описание не обязательно
    if len(description) > 500:
        return False
    return True

def clean_text(text: str) -> str:
    """Очистка текста от лишних пробелов и символов"""
    if not text:
        return ""
    # Убираем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def get_user_info_string(user) -> str:
    """Получение строки с информацией о пользователе"""
    parts = []
    if hasattr(user, 'first_name') and user.first_name:
        parts.append(user.first_name)
    if hasattr(user, 'last_name') and user.last_name:
        parts.append(user.last_name)
    if hasattr(user, 'username') and user.username:
        parts.append(f"@{user.username}")
    
    if parts:
        return " ".join(parts) + f" (ID: {user.id})"
    return f"ID: {user.id}"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Обрезка текста с добавлением многоточия"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..." 