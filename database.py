import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from config import DATABASE_URL

class Database:
    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    theme TEXT,
                    place TEXT,
                    contact TEXT,
                    event_time TEXT,
                    photo_file_id TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'creating',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_message_id INTEGER,
                    channel_message_id INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT,
                    event_id INTEGER,
                    data TEXT,
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            ''')
    
    def create_event(self, user_id: int, username: str = None) -> int:
        """Создание нового события"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'INSERT INTO events (user_id, username, status) VALUES (?, ?, ?)',
                (user_id, username, 'creating')
            )
            return cursor.lastrowid
    
    def update_event(self, event_id: int, **kwargs):
        """Обновление события"""
        if not kwargs:
            return
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['theme', 'place', 'contact', 'event_time', 'photo_file_id', 'description', 'status', 'admin_message_id', 'channel_message_id']:
                fields.append(f'{key} = ?')
                values.append(value)
        
        if fields:
            fields.append('updated_at = ?')
            values.append(datetime.now().isoformat())
            values.append(event_id)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    f'UPDATE events SET {", ".join(fields)} WHERE id = ?',
                    values
                )
    
    def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получение события по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_current_event(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение текущего события пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM events WHERE user_id = ? AND status = "creating" ORDER BY created_at DESC LIMIT 1',
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def set_user_state(self, user_id: int, state: str, event_id: int = None, data: Dict = None):
        """Установка состояния пользователя"""
        data_json = json.dumps(data) if data else None
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO user_states (user_id, state, event_id, data) VALUES (?, ?, ?, ?)',
                (user_id, state, event_id, data_json)
            )
    
    def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение состояния пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM user_states WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result['data']:
                    result['data'] = json.loads(result['data'])
                return result
            return None
    
    def clear_user_state(self, user_id: int):
        """Очистка состояния пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM user_states WHERE user_id = ?', (user_id,))

# Глобальный экземпляр базы данных
db = Database() 