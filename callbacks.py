import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import db
from config import STATES, ADMIN_CHAT_ID, CHANNEL_ID
from keyboards import get_main_menu_keyboard, get_admin_moderation_keyboard
from utils import format_event_announcement, format_admin_preview, get_user_info_string
from handlers import show_event_preview

logger = logging.getLogger(__name__)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик callback-запросов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    logger.info(f"Callback received: data='{data}', user_id={user_id}, chat_id={query.message.chat.id}")
    
    try:
        if data.startswith('edit_'):
            logger.info(f"Routing to edit handler")
            await handle_edit_callback(update, context, data)
        elif data.startswith('submit_'):
            logger.info(f"Routing to submit handler")
            await handle_submit_callback(update, context, data)
        elif data.startswith('cancel_'):
            logger.info(f"Routing to cancel handler")
            await handle_cancel_callback(update, context, data)
        elif data.startswith('approve_'):
            logger.info(f"Routing to approve handler")
            await handle_approve_callback(update, context, data)
        elif data.startswith('reject_'):
            logger.info(f"Routing to reject handler")
            await handle_reject_callback(update, context, data)
        elif data == 'skip_photo':
            logger.info(f"Routing to skip photo handler")
            await handle_skip_photo_callback(update, context)
        elif data == 'cancel_creation':
            logger.info(f"Routing to cancel creation handler")
            await handle_cancel_creation_callback(update, context)
        else:
            logger.warning(f"Unknown callback data: {data}")
    except Exception as e:
        logger.error(f"Error handling callback {data}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")

async def handle_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка редактирования полей события"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Парсим данные: edit_{field}_{event_id}
    parts = data.split('_')
    field = parts[1]
    event_id = int(parts[2])
    
    # Проверяем права доступа
    event = db.get_event(event_id)
    if not event or event['user_id'] != user_id:
        await query.edit_message_text("❌ Событие не найдено или у вас нет прав доступа")
        return
    
    # Устанавливаем состояние редактирования
    edit_data = {'field': field, 'event_id': event_id}
    db.set_user_state(user_id, STATES['EDITING'], event_id, edit_data)
    
    # Отправляем запрос на ввод
    field_names = {
        'theme': 'тему события',
        'place': 'место проведения',
        'contact': 'контакт для связи',
        'time': 'время проведения',
        'photo': 'фото события',
        'description': 'описание события'
    }
    
    field_name = field_names.get(field, field)
    
    # Проверяем, есть ли фото в сообщении для всех полей
    if query.message.photo:
        # Для сообщений с фото используем edit_message_caption
        if field == 'photo':
            await query.edit_message_caption(
                caption="📝 Отправь новое фото для события или напиши 'удалить' чтобы убрать фото"
            )
        else:
            await query.edit_message_caption(
                caption=f"📝 Введи новое значение для поля '{field_name}':"
            )
    else:
        # Для обычных текстовых сообщений
        if field == 'photo':
            await query.edit_message_text(
                "📝 Отправь новое фото для события или напиши 'удалить' чтобы убрать фото"
            )
        else:
            await query.edit_message_text(
                f"📝 Введи новое значение для поля '{field_name}':"
            )

async def handle_editing_input(update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: dict, text: str):
    """Обработка ввода при редактировании"""
    user_id = update.effective_user.id
    edit_data = user_state.get('data', {})
    field = edit_data.get('field')
    event_id = edit_data.get('event_id')
    
    if not field or not event_id:
        await update.message.reply_text("❌ Ошибка редактирования")
        return
    
    # Валидация и сохранение
    success = False
    
    if field == 'theme':
        from utils import validate_theme
        if validate_theme(text):
            db.update_event(event_id, theme=text)
            success = True
    elif field == 'place':
        from utils import validate_place
        if validate_place(text):
            db.update_event(event_id, place=text)
            success = True
    elif field == 'contact':
        from utils import validate_contact
        if validate_contact(text):
            db.update_event(event_id, contact=text)
            success = True
    elif field == 'time':
        from utils import validate_time
        if validate_time(text):
            db.update_event(event_id, event_time=text)
            success = True
    elif field == 'description':
        from utils import validate_description
        if text.lower() == 'удалить':
            db.update_event(event_id, description=None)
            success = True
        elif validate_description(text):
            db.update_event(event_id, description=text)
            success = True
    
    if success:
        await update.message.reply_text("✅ Изменения сохранены!")
        # Показываем обновленный предпросмотр
        await show_event_preview(update, context, event_id)
    else:
        await update.message.reply_text("❌ Некорректное значение. Попробуйте еще раз.")

async def handle_photo_editing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования фото"""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if not user_state or user_state['state'] != STATES['EDITING']:
        return
    
    edit_data = user_state.get('data', {})
    if edit_data.get('field') != 'photo':
        return
    
    # Проверяем, что это именно фото
    if not update.message.photo:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте именно фото.\n\n"
            "Поддерживаемые форматы: .png, .jpeg, .jpg"
        )
        return
    
    event_id = edit_data.get('event_id')
    photo = update.message.photo[-1]
    
    # Сохраняем новое фото
    db.update_event(event_id, photo_file_id=photo.file_id)
    
    await update.message.reply_text("✅ Фото обновлено!")
    await show_event_preview(update, context, event_id)

async def handle_submit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка отправки на модерацию"""
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"Submit callback: data={data}, user_id={user_id}")
    
    # Парсим event_id
    event_id = int(data.split('_')[1])
    logger.info(f"Parsed event_id: {event_id}")
    
    # Проверяем права доступа
    event = db.get_event(event_id)
    if not event:
        logger.error(f"Event {event_id} not found")
        await query.edit_message_text("❌ Событие не найдено")
        return
    
    if event['user_id'] != user_id:
        logger.error(f"Access denied: event user_id={event['user_id']}, query user_id={user_id}")
        await query.edit_message_text("❌ У вас нет прав доступа")
        return
    
    logger.info(f"Starting moderation process for event {event_id}")
    # Отправляем на модерацию
    await send_to_moderation(query, context, event)

async def send_to_moderation(query, context, event):
    """Отправка события на модерацию администратору"""
    try:
        logger.info(f"Preparing admin message for event {event['id']}")
        user_info = get_user_info_string(query.from_user)
        admin_text = format_admin_preview(event, user_info)
        
        logger.info(f"Sending to admin chat {ADMIN_CHAT_ID}")
        
        # Отправляем администратору
        if event['photo_file_id']:
            logger.info("Sending admin message with photo")
            admin_message = await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=event['photo_file_id'],
                caption=admin_text,
                parse_mode='HTML',
                reply_markup=get_admin_moderation_keyboard(event['id'])
            )
        else:
            logger.info("Sending admin message without photo")
            admin_message = await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text,
                parse_mode='HTML',
                reply_markup=get_admin_moderation_keyboard(event['id'])
            )
        
        logger.info(f"Admin message sent successfully, message_id: {admin_message.message_id}")
        
        # Сохраняем ID сообщения администратора
        db.update_event(event['id'], 
                       status='pending', 
                       admin_message_id=admin_message.message_id)
        
        # Очищаем состояние пользователя
        db.clear_user_state(query.from_user.id)
        
        # Уведомляем пользователя
        if query.message.photo:
            await query.edit_message_caption(
                caption="✅ Анонс отправлен на модерацию!\n\n"
                       "Ты получишь уведомление, как только администратор рассмотрит заявку.",
                reply_markup=None
            )
        else:
            await query.edit_message_text(
                "✅ Анонс отправлен на модерацию!\n\n"
                "Ты получишь уведомление, как только администратор рассмотрит заявку.",
                reply_markup=None
            )
        
        # Показываем главное меню
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error sending to moderation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Правильно показываем ошибку в зависимости от типа сообщения
        if query.message.photo:
            await query.edit_message_caption(
                caption="❌ Ошибка при отправке на модерацию",
                reply_markup=None
            )
        else:
            await query.edit_message_text("❌ Ошибка при отправке на модерацию")

async def handle_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка одобрения анонса администратором"""
    query = update.callback_query
    logger.info(f"Approve callback received from chat {query.message.chat.id}, admin chat: {ADMIN_CHAT_ID}")
    
    # Проверяем, что сообщение пришло из админ-чата
    if str(query.message.chat.id) != str(ADMIN_CHAT_ID):
        logger.warning(f"Access denied for chat {query.message.chat.id}")
        await query.answer("❌ У вас нет прав администратора")
        return
    
    event_id = int(data.split('_')[1])
    event = db.get_event(event_id)
    logger.info(f"Processing approve for event {event_id}")
    
    if not event:
        await query.edit_message_text("❌ Событие не найдено")
        return
    
    try:
        # Публикуем в канал
        announcement_text = format_event_announcement(event)
        
        if event['photo_file_id']:
            channel_message = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=event['photo_file_id'],
                caption=announcement_text,
                parse_mode='HTML'
            )
        else:
            channel_message = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=announcement_text,
                parse_mode='HTML'
            )
        
        # Обновляем статус события
        db.update_event(event_id, 
                       status='published', 
                       channel_message_id=channel_message.message_id)
        
        # Уведомляем администратора
        await query.edit_message_text(
            f"✅ <b>АНОНС ОПУБЛИКОВАН</b>\n\n"
            f"Событие #{event_id} успешно опубликовано в канале!",
            parse_mode='HTML',
            reply_markup=None
        )
        
        # Уведомляем автора
        await context.bot.send_message(
            chat_id=event['user_id'],
            text=f"🎉 <b>Отличные новости!</b>\n\n"
                 f"Твой анонс '{event['theme']}' одобрен и опубликован в канале!\n\n"
                 f"Спасибо за участие! 🙌",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error approving event: {e}")
        await query.edit_message_text("❌ Ошибка при публикации")

async def handle_reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка отклонения анонса администратором"""
    query = update.callback_query
    logger.info(f"Reject callback received from chat {query.message.chat.id}, admin chat: {ADMIN_CHAT_ID}")
    
    # Проверяем, что сообщение пришло из админ-чата
    if str(query.message.chat.id) != str(ADMIN_CHAT_ID):
        logger.warning(f"Access denied for chat {query.message.chat.id}")
        await query.answer("❌ У вас нет прав администратора")
        return
    
    event_id = int(data.split('_')[1])
    event = db.get_event(event_id)
    logger.info(f"Processing reject for event {event_id}")
    
    if not event:
        await query.edit_message_text("❌ Событие не найдено")
        return
    
    # Обновляем статус
    db.update_event(event_id, status='rejected')
    
    # Уведомляем администратора
    await query.edit_message_text(
        f"❌ <b>АНОНС ОТКЛОНЕН</b>\n\n"
        f"Событие #{event_id} отклонено.",
        parse_mode='HTML',
        reply_markup=None
    )
    
    # Уведомляем автора
    await context.bot.send_message(
        chat_id=event['user_id'],
        text=f"😔 К сожалению, твой анонс '{event['theme']}' не прошел модерацию.\n\n"
             f"Ты можешь создать новый анонс, исправив замечания."
    )

async def handle_skip_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка пропуска фото"""
    query = update.callback_query
    user_id = query.from_user.id
    user_state = db.get_user_state(user_id)
    
    if not user_state or user_state['state'] != STATES['WAITING_PHOTO']:
        await query.answer("❌ Неверное состояние")
        return
    
    event_id = user_state['event_id']
    
    # Переходим к описанию
    db.set_user_state(user_id, STATES['WAITING_DESCRIPTION'], event_id)
    
    await query.edit_message_text(
        "6️⃣ Добавьте короткое описание прогулки\n"
        "Расскажите, что планируете делать, что взять с собой (максимум 500 символов):"
    )

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка отмены создания конкретного события"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Очищаем состояние
    db.clear_user_state(user_id)
    
    # Правильно редактируем сообщение в зависимости от типа
    if query.message.photo:
        await query.edit_message_caption(
            caption="❌ Создание анонса отменено.",
            reply_markup=None
        )
    else:
        await query.edit_message_text(
            "❌ Создание анонса отменено.",
            reply_markup=None
        )
    
    # Показываем главное меню
    await context.bot.send_message(
        chat_id=user_id,
        text="Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_cancel_creation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка общей отмены создания"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Очищаем состояние
    db.clear_user_state(user_id)
    
    # Правильно редактируем сообщение в зависимости от типа
    if query.message.photo:
        await query.edit_message_caption(
            caption="❌ Создание анонса отменено.",
            reply_markup=None
        )
    else:
        await query.edit_message_text(
            "❌ Создание анонса отменено.",
            reply_markup=None
        )
    
    # Показываем главное меню
    await context.bot.send_message(
        chat_id=user_id,
        text="Главное меню:",
        reply_markup=get_main_menu_keyboard()
    ) 