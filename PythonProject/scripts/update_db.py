#!/usr/bin/env python3
"""
Скрипт для обновления структуры базы данных
"""

import sqlite3

def update_database():
    """Обновление структуры базы данных"""
    
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    try:
        # Добавляем колонку password если её нет
        cursor.execute('ALTER TABLE masters ADD COLUMN password TEXT DEFAULT "master123"')
        print("✅ Колонка password добавлена в таблицу masters")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ Колонка password уже существует")
        else:
            print(f"❌ Ошибка: {e}")
    
    conn.commit()
    conn.close()
    print("✅ База данных обновлена!")

if __name__ == "__main__":
    update_database()
