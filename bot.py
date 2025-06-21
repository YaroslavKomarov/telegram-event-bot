import logging
import asyncio
import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import BOT_TOKEN
from handlers import (
    start_command, help_command, cancel_command,
    handle_text_message, handle_photo_input, handle_invalid_media
)
from callbacks import handle_callback_query, handle_photo_editing, handle_editing_input
from health import start_health_server

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_application():
    """Создание и настройка приложения бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Обработчик callback-кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Обработчик фотографий
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_messages))
    
    # Обработчики неподходящих типов медиа
    application.add_handler(MessageHandler(filters.VIDEO, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.ANIMATION, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.VOICE, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.AUDIO, handle_invalid_media_messages))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_invalid_media_messages))
    
    # Обработчик текстовых сообщений (должен быть последним)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    return application

async def handle_photo_messages(update, context):
    """Маршрутизация фото-сообщений"""
    from database import db
    from config import STATES
    
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if not user_state:
        return
    
    if user_state['state'] == STATES['WAITING_PHOTO']:
        await handle_photo_input(update, context)
    elif user_state['state'] == STATES['EDITING']:
        await handle_photo_editing(update, context)

async def handle_invalid_media_messages(update, context):
    """Маршрутизация неподходящих медиа-сообщений"""
    await handle_invalid_media(update, context)

async def error_handler(update, context):
    """Обработчик ошибок"""
    logger.error(f'Update {update} caused error {context.error}')

def main():
    """Главная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    logger.info("Starting Event Announcement Bot...")
    
    # Запускаем health check сервер для Railway
    port = int(os.getenv('PORT', 8080))
    start_health_server(port)
    
    # Создаем приложение
    application = create_application()
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main() 