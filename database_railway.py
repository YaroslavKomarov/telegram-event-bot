import os
import json
import logging
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Подключение к PostgreSQL базе данных"""
        try:
            # Railway автоматически предоставляет переменную DATABASE_URL
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
            else:
                # Fallback на отдельные переменные
                self.connection = psycopg2.connect(
                    host=os.getenv('PGHOST', 'localhost'),
                    database=os.getenv('PGDATABASE', 'railway'),
                    user=os.getenv('PGUSER', 'postgres'),
                    password=os.getenv('PGPASSWORD', ''),
                    port=os.getenv('PGPORT', 5432)
                )
            
            self.connection.autocommit = True
            logger.info("✅ Подключение к PostgreSQL установлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    def create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.connection.cursor()
        
        try:
            # Таблица событий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    theme VARCHAR(100) NOT NULL,
                    place VARCHAR(500) NOT NULL,
                    contact VARCHAR(100) NOT NULL,
                    event_time VARCHAR(100) NOT NULL,
                    photo_file_id VARCHAR(255),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'draft',
                    admin_message_id BIGINT,
                    channel_message_id BIGINT
                )
            ''')
            
            # Таблица состояний пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id BIGINT PRIMARY KEY,
                    state VARCHAR(50) NOT NULL,
                    event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индексы для производительности
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_states_user_id ON user_states(user_id)')
            
            logger.info("✅ Таблицы созданы успешно")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            raise
        finally:
            cursor.close()

    def create_event(self, user_id: int, theme: str, place: str, contact: str, 
                    event_time: str, photo_file_id: str = None, description: str = None) -> int:
        """Создание нового события"""
        cursor = self.connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO events (user_id, theme, place, contact, event_time, photo_file_id, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (user_id, theme, place, contact, event_time, photo_file_id, description))
            
            event_id = cursor.fetchone()[0]
            logger.info(f"✅ Событие {event_id} создано для пользователя {user_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания события: {e}")
            raise
        finally:
            cursor.close()

    def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получение события по ID"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM events WHERE id = %s', (event_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения события {event_id}: {e}")
            return None
        finally:
            cursor.close()

    def update_event(self, event_id: int, **kwargs) -> bool:
        """Обновление события"""
        if not kwargs:
            return True
            
        cursor = self.connection.cursor()
        try:
            # Формируем SET часть запроса
            set_parts = []
            values = []
            
            for key, value in kwargs.items():
                set_parts.append(f"{key} = %s")
                values.append(value)
            
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
            values.append(event_id)
            
            query = f"UPDATE events SET {', '.join(set_parts)} WHERE id = %s"
            cursor.execute(query, values)
            
            success = cursor.rowcount > 0
            if success:
                logger.info(f"✅ Событие {event_id} обновлено: {kwargs}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления события {event_id}: {e}")
            return False
        finally:
            cursor.close()

    def get_user_events(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение событий пользователя"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('''
                SELECT * FROM events 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий пользователя {user_id}: {e}")
            return []
        finally:
            cursor.close()

    def set_user_state(self, user_id: int, state: str, event_id: int = None, data: dict = None):
        """Установка состояния пользователя"""
        cursor = self.connection.cursor()
        try:
            data_json = json.dumps(data) if data else None
            
            cursor.execute('''
                INSERT INTO user_states (user_id, state, event_id, data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    state = EXCLUDED.state,
                    event_id = EXCLUDED.event_id,
                    data = EXCLUDED.data,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, state, event_id, data_json))
            
            logger.info(f"✅ Состояние пользователя {user_id} установлено: {state}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки состояния для {user_id}: {e}")
        finally:
            cursor.close()

    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение состояния пользователя"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('SELECT * FROM user_states WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            
            if result:
                state_dict = dict(result)
                if state_dict['data']:
                    state_dict['data'] = json.loads(state_dict['data'])
                return state_dict
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения состояния пользователя {user_id}: {e}")
            return None
        finally:
            cursor.close()

    def clear_user_state(self, user_id: int):
        """Очистка состояния пользователя"""
        cursor = self.connection.cursor()
        try:
            cursor.execute('DELETE FROM user_states WHERE user_id = %s', (user_id,))
            logger.info(f"✅ Состояние пользователя {user_id} очищено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки состояния для {user_id}: {e}")
        finally:
            cursor.close()

    def delete_event(self, event_id: int) -> bool:
        """Удаление события"""
        cursor = self.connection.cursor()
        try:
            cursor.execute('DELETE FROM events WHERE id = %s', (event_id,))
            success = cursor.rowcount > 0
            if success:
                logger.info(f"✅ Событие {event_id} удалено")
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления события {event_id}: {e}")
            return False
        finally:
            cursor.close()

    def get_pending_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение событий на модерации"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute('''
                SELECT * FROM events 
                WHERE status = 'pending' 
                ORDER BY created_at ASC 
                LIMIT %s
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий на модерации: {e}")
            return []
        finally:
            cursor.close()

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("✅ Соединение с БД закрыто")

# Создаем глобальный экземпляр для использования в модулях
db = DatabaseManager() 