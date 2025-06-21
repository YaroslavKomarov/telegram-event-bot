import sqlite3
import os
from config import DATABASE_URL

def migrate_database():
    """Миграция базы данных - добавление поля contact"""
    
    # Проверяем, существует ли база данных
    if not os.path.exists(DATABASE_URL):
        print("База данных не найдена. Создастся автоматически при первом запуске.")
        return
    
    try:
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже колонка contact
            cursor.execute("PRAGMA table_info(events)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'contact' not in columns:
                # Добавляем колонку contact
                cursor.execute('ALTER TABLE events ADD COLUMN contact TEXT')
                print("✅ Добавлена колонка 'contact' в таблицу events")
            else:
                print("ℹ️ Колонка 'contact' уже существует")
                
            conn.commit()
            print("✅ Миграция базы данных завершена успешно")
            
    except Exception as e:
        print(f"❌ Ошибка при миграции базы данных: {e}")

if __name__ == "__main__":
    migrate_database() 