from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    """Главное меню бота"""
    keyboard = [
        [KeyboardButton("📣 Пригласить на прогулку")],
        [KeyboardButton("📋 Мои анонсы"), KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_preview_keyboard(event_id: int):
    """Клавиатура для предпросмотра анонса"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Изменить тему", callback_data=f"edit_theme_{event_id}"),
            InlineKeyboardButton("📍 Изменить место", callback_data=f"edit_place_{event_id}")
        ],
        [
            InlineKeyboardButton("📞 Изменить контакт", callback_data=f"edit_contact_{event_id}"),
            InlineKeyboardButton("🕐 Изменить время", callback_data=f"edit_time_{event_id}")
        ],
        [
            InlineKeyboardButton("🖼 Изменить фото", callback_data=f"edit_photo_{event_id}"),
            InlineKeyboardButton("📝 Изменить описание", callback_data=f"edit_description_{event_id}")
        ],
        [
            InlineKeyboardButton("✅ Отправить на модерацию", callback_data=f"submit_{event_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{event_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_moderation_keyboard(event_id: int):
    """Клавиатура для модерации администратором"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"approve_{event_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{event_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_skip_photo_keyboard():
    """Клавиатура для пропуска фото"""
    keyboard = [
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_photo")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура для отмены создания"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить создание", callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(keyboard) 