#!/usr/bin/env python3
import sqlite3

def check_all_schedule():
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    print("=== ВСЕ ЗАПИСИ В РАСПИСАНИИ ===")
    cursor.execute('SELECT COUNT(*) FROM schedule')
    count = cursor.fetchone()[0]
    print(f"Всего записей в schedule: {count}")
    
    if count > 0:
        cursor.execute('SELECT * FROM schedule LIMIT 10')
        schedule = cursor.fetchall()
        print("Первые 10 записей:")
        for s in schedule:
            print(f"ID: {s[0]}, Master ID: {s[1]}, Дата: {s[2]}, Время: {s[3]}-{s[4]}")
    
    print("\n=== ПРОВЕРКА МАСТЕРОВ ===")
    cursor.execute('SELECT id, name FROM masters')
    masters = cursor.fetchall()
    print("Все мастера:")
    for m in masters:
        print(f"ID: {m[0]}, Имя: {m[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_all_schedule()
