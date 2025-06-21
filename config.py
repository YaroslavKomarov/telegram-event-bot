import os
from dotenv import load_dotenv

load_dotenv()

# Токены и идентификаторы
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # ID чата администраторов
CHANNEL_ID = os.getenv('CHANNEL_ID')  # ID канала для публикации

# Конфигурация базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'events.db')

# Максимальные размеры
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TEXT_LENGTH = 2000

# Состояния для FSM
STATES = {
    'WAITING_THEME': 'waiting_theme',
    'WAITING_PLACE': 'waiting_place',
    'WAITING_CONTACT': 'waiting_contact',
    'WAITING_TIME': 'waiting_time',
    'WAITING_PHOTO': 'waiting_photo',
    'WAITING_DESCRIPTION': 'waiting_description',
    'PREVIEW': 'preview',
    'EDITING': 'editing'
} 