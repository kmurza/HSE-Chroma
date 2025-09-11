#!/usr/bin/env python3
import sqlite3

def add_sept8_schedule():
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    # Добавляем расписание на 8 сентября для всех мастеров
    masters = [25, 26, 27, 28]  # ID мастеров
    
    for master_id in masters:
        cursor.execute('''
            INSERT INTO schedule (master_id, date, start_time, end_time, is_available)
            VALUES (?, '2025-09-08', '09:00', '18:00', 1)
        ''', (master_id,))
        print(f"Добавлено расписание для мастера {master_id} на 8 сентября")
    
    conn.commit()
    conn.close()
    print("✅ Расписание на 8 сентября добавлено!")

if __name__ == "__main__":
    add_sept8_schedule()
