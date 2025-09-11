#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

def check_alexandra_schedule():
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    print("=== РАСПИСАНИЕ АЛЕКСАНДРЫ МУР ===")
    cursor.execute('''
        SELECT date, start_time, end_time 
        FROM schedule 
        WHERE master_id = 21 
        ORDER BY date, start_time
    ''')
    schedule = cursor.fetchall()
    
    print(f"Всего записей в расписании: {len(schedule)}")
    for s in schedule:
        print(f"Дата: {s[0]}, Время: {s[1]} - {s[2]}")
    
    print("\n=== ПРОВЕРКА ДАТЫ 8 СЕНТЯБРЯ ===")
    cursor.execute('''
        SELECT date, start_time, end_time 
        FROM schedule 
        WHERE master_id = 21 AND date = '2025-09-08'
    ''')
    sept_8 = cursor.fetchall()
    print(f"Записей на 8 сентября: {len(sept_8)}")
    for s in sept_8:
        print(f"8 сентября: {s[1]} - {s[2]}")
    
    print("\n=== ПРОВЕРКА ДАТЫ 9 СЕНТЯБРЯ ===")
    cursor.execute('''
        SELECT date, start_time, end_time 
        FROM schedule 
        WHERE master_id = 21 AND date = '2025-09-09'
    ''')
    sept_9 = cursor.fetchall()
    print(f"Записей на 9 сентября: {len(sept_9)}")
    for s in sept_9:
        print(f"9 сентября: {s[1]} - {s[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_alexandra_schedule()
