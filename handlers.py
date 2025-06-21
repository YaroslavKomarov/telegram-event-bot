import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import db
from config import STATES, ADMIN_CHAT_ID, CHANNEL_ID, MAX_TEXT_LENGTH
from keyboards import (
    get_main_menu_keyboard, get_preview_keyboard, get_admin_moderation_keyboard,
    get_skip_photo_keyboard, get_cancel_keyboard
)
from utils import (
    format_event_announcement, format_admin_preview, get_user_info_string,
    validate_theme, validate_place, validate_contact, validate_time, validate_description, clean_text
)

logger = logging.getLogger(__name__)

# Команды бота
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я помогу тебе создать анонс для прогулки
и опубликовать его в канале «Айда гулять, Нови-Сад!»

Давай начнем! Нажми кнопку «📣 Пригласить на прогулку», чтобы создать анонс!
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
ℹ️ Как пользоваться ботом:

1. Нажми "📣 Пригласить на прогулку"
2. Пошагово заполни все поля:
   • Тема события
   • Место проведения
   • Время проведения
   • Фото (необязательно)
   • Описание (необязательно)
3. Проверь предпросмотр и отправь на модерацию
4. Дождись одобрения администратора
5. Получи уведомление о публикации

**Команды:**
/start - Начать работу
/help - Справка
/cancel - Отменить создание анонса
    """
    
    await update.message.reply_text(help_text)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel"""
    user_id = update.effective_user.id
    db.clear_user_state(user_id)
    
    await update.message.reply_text(
        "❌ Создание анонса отменено.",
        reply_markup=get_main_menu_keyboard()
    )

# Обработчики текстовых сообщений
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем нажатие кнопок главного меню
    if text == "📣 Пригласить на прогулку":
        await start_event_creation(update, context)
    elif text == "📋 Мои анонсы":
        await show_user_events(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    else:
        # Обрабатываем состояния пользователя
        user_state = db.get_user_state(user_id)
        if not user_state:
            await update.message.reply_text(
                "Используй кнопки меню для взаимодействия с ботом 👇",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await handle_user_input(update, context, user_state)

async def start_event_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания события"""
    user = update.effective_user
    user_id = user.id
    
    # Создаем новое событие
    event_id = db.create_event(user_id, user.username)
    
    # Устанавливаем состояние
    db.set_user_state(user_id, STATES['WAITING_THEME'], event_id)
    
    await update.message.reply_text(
        "🎉 Отлично! Давай создадим анонс события.\n\n"
        "1️⃣ Какая тема у нашей прогулки? Например:\n"
        "'Прогулка по центру города' или 'Встреча в парке'",
        reply_markup=get_cancel_keyboard()
    )

async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_state):
    """Обработка ввода пользователя в зависимости от состояния"""
    user_id = update.effective_user.id
    text = clean_text(update.message.text)
    state = user_state['state']
    event_id = user_state['event_id']
    
    if state == STATES['WAITING_THEME']:
        await handle_theme_input(update, context, event_id, text)
    elif state == STATES['WAITING_PLACE']:
        await handle_place_input(update, context, event_id, text)
    elif state == STATES['WAITING_CONTACT']:
        await handle_contact_input(update, context, event_id, text)
    elif state == STATES['WAITING_TIME']:
        await handle_time_input(update, context, event_id, text)
    elif state == STATES['WAITING_DESCRIPTION']:
        await handle_description_input(update, context, event_id, text)
    elif state == STATES['EDITING']:
        from callbacks import handle_editing_input
        await handle_editing_input(update, context, user_state, text)

async def handle_theme_input(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, text: str):
    """Обработка ввода темы"""
    user_id = update.effective_user.id
    
    if not validate_theme(text):
        await update.message.reply_text(
            "❌ Тема должна содержать от 3 до 100 символов. Попробуй еще раз:"
        )
        return
    
    # Сохраняем тему
    db.update_event(event_id, theme=text)
    
    # Переходим к следующему шагу
    db.set_user_state(user_id, STATES['WAITING_PLACE'], event_id)
    
    await update.message.reply_text(
        f"✅ Тема сохранена: {text}\n\n"
        "2️⃣ Где встречаемся?\n\n"
        "🗺 Лучший вариант: Скопируй ссылку из Google Maps\n"
        "📝 Альтернатива: Напиши адрес текстом\n"
        "💡 Совет: Можно написать название места и на следующей строке добавить ссылку\n\n"
        "Примеры:\n"
        "• https://maps.google.com/...\n"
        "• Парк Горького, главный вход\n"
        "• Кафе 'Пушкин'\nhttps://maps.google.com/...",
        reply_markup=get_cancel_keyboard()
    )

async def handle_place_input(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, text: str):
    """Обработка ввода места"""
    user_id = update.effective_user.id
    
    if not validate_place(text):
        await update.message.reply_text(
            "❌ Место должно содержать от 3 до 500 символов. Попробуй еще раз:"
        )
        return
    
    # Сохраняем место
    db.update_event(event_id, place=text)
    
    # Переходим к следующему шагу
    db.set_user_state(user_id, STATES['WAITING_CONTACT'], event_id)
    
    await update.message.reply_text(
        f"✅ Место сохранено: {text}\n\n"
        "3️⃣ Контакт для связи\n\n"
        "Оставьте контакт для связи (ваш username в Telegram или номер телефона). "
        "Он будет виден всем в анонсе.\n\n"
        "Примеры:\n"
        "• @username\n"
        "• +7 900 123-45-67\n"
        "• Анна, @anna_walk",
        reply_markup=get_cancel_keyboard()
    )

async def handle_contact_input(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, text: str):
    """Обработка ввода контакта"""
    user_id = update.effective_user.id
    
    if not validate_contact(text):
        await update.message.reply_text(
            "❌ Контакт должен содержать от 3 до 100 символов. Попробуй еще раз:"
        )
        return
    
    # Сохраняем контакт
    db.update_event(event_id, contact=text)
    
    # Переходим к следующему шагу
    db.set_user_state(user_id, STATES['WAITING_TIME'], event_id)
    
    await update.message.reply_text(
        f"✅ Контакт сохранен: {text}\n\n"
        "4️⃣ Когда встречаемся?\n\n"
        "Укажите дату и время события.\n\n"
        "Примеры:\n"
        "• 25 декабря, 12:30\n"
        "• Завтра в 18:00\n"
        "• Суббота, 15 декабря в 14:00",
        reply_markup=get_cancel_keyboard()
    )

async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, text: str):
    """Обработка ввода времени"""
    user_id = update.effective_user.id
    
    if not validate_time(text):
        await update.message.reply_text(
            "❌ Время должно содержать от 3 до 100 символов. Попробуй еще раз:"
        )
        return
    
    # Сохраняем время
    db.update_event(event_id, event_time=text)
    
    # Переходим к следующему шагу
    db.set_user_state(user_id, STATES['WAITING_PHOTO'], event_id)
    
    await update.message.reply_text(
        f"✅ Время сохранено: {text}\n\n"
        "5️⃣ Супер! Теперь загрузите фото или картинку для анонса. Форматы: .png, .jpeg, .jpg\n"
        "Если хотите продолжить без изображения, нажмите кнопку «Пропустить»",
        reply_markup=get_skip_photo_keyboard()
    )

async def handle_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загрузки фото"""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if not user_state or user_state['state'] != STATES['WAITING_PHOTO']:
        return
    
    event_id = user_state['event_id']
    
    # Получаем фото наилучшего качества
    photo = update.message.photo[-1]
    
    # Проверяем размер фото (Telegram автоматически ограничивает размер)
    # Дополнительная проверка не требуется, так как Telegram сжимает фото
    
    # Сохраняем file_id фото
    db.update_event(event_id, photo_file_id=photo.file_id)
    
    # Переходим к описанию
    db.set_user_state(user_id, STATES['WAITING_DESCRIPTION'], event_id)
    
    await update.message.reply_text(
        "✅ Фото сохранено!\n\n"
        "6️⃣ Добавьте короткое описание прогулки\n"
        "Расскажите, что планируете делать, что взять с собой (максимум 500 символов):",
        reply_markup=get_cancel_keyboard()
    )

async def handle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, text: str):
    """Обработка ввода описания"""
    user_id = update.effective_user.id
    
    if text == "/skip":
        description = None
    else:
        if not validate_description(text):
            await update.message.reply_text(
                f"❌ Ваше описание слишком длинное ({len(text)}/500 символов). Пожалуйста, сократите его и отправьте снова."
            )
            return
        description = text
    
    # Сохраняем описание
    db.update_event(event_id, description=description)
    
    # Показываем предпросмотр
    await show_event_preview(update, context, event_id)

async def show_event_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Показ предпросмотра события"""
    user_id = update.effective_user.id
    event = db.get_event(event_id)
    
    if not event:
        await update.message.reply_text("❌ Событие не найдено")
        return
    
    # Очищаем состояние
    db.set_user_state(user_id, STATES['PREVIEW'], event_id)
    
    # Формируем предпросмотр
    preview_text = "🎯 <b>ПРЕДПРОСМОТР АНОНСА</b>\n\n" + format_event_announcement(event)
    
    if event['photo_file_id']:
        await update.message.reply_photo(
            photo=event['photo_file_id'],
            caption=preview_text,
            parse_mode='HTML',
            reply_markup=get_preview_keyboard(event_id)
        )
    else:
        await update.message.reply_text(
            preview_text,
            parse_mode='HTML',
            reply_markup=get_preview_keyboard(event_id)
        )

async def handle_invalid_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неподходящих типов медиа при загрузке фото"""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    # Проверяем, ожидает ли бот фото
    if user_state and user_state['state'] == STATES['WAITING_PHOTO']:
        # Определяем тип медиа для более точного сообщения
        media_type = "файл"
        if update.message.video:
            media_type = "видео"
        elif update.message.sticker:
            media_type = "стикер"
        elif update.message.document:
            # Проверяем, не является ли документ изображением
            doc = update.message.document
            if doc.mime_type and doc.mime_type.startswith('image/'):
                media_type = "документ-изображение (отправьте как фото, а не документ)"
            else:
                media_type = "документ"
        elif update.message.animation:
            media_type = "GIF"
        elif update.message.voice:
            media_type = "голосовое сообщение"
        elif update.message.audio:
            media_type = "аудио"
        elif update.message.video_note:
            media_type = "видеосообщение"
        
        await update.message.reply_text(
            f"❌ Пожалуйста, отправьте именно фото (не {media_type}).\n\n"
            "Поддерживаемые форматы: .png, .jpeg, .jpg",
            reply_markup=get_skip_photo_keyboard()
        )
    elif user_state and user_state['state'] == STATES['EDITING']:
        # Проверяем, редактируется ли фото
        edit_data = user_state.get('data', {})
        if edit_data.get('field') == 'photo':
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте именно фото (не видео или стикер).\n\n"
                "Поддерживаемые форматы: .png, .jpeg, .jpg"
            )

async def show_user_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ событий пользователя"""
    await update.message.reply_text(
        "📋 В разработке...\n"
        "Скоро здесь будет список твоих анонсов!"
    ) 