#!/usr/bin/env python3
import sqlite3

def check_users():
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    print("=== ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ ===")
    cursor.execute('SELECT * FROM users WHERE user_id = 963051276')
    users = cursor.fetchall()
    print(f"Пользователь 963051276: {users}")
    
    print("\n=== ПРОВЕРКА МАСТЕРОВ ===")
    cursor.execute('SELECT * FROM masters WHERE id = 21')
    masters = cursor.fetchall()
    print(f"Мастер 21: {masters}")
    
    print("\n=== ПРОВЕРКА УСЛУГ ===")
    cursor.execute('SELECT * FROM services WHERE id = 82')
    services = cursor.fetchall()
    print(f"Услуга 82: {services}")
    
    print("\n=== ПРОВЕРКА JOIN ЗАПРОСА ===")
    cursor.execute('''
        SELECT a.*, u.first_name, m.name as master_name, s.name as service_name, s.duration, m.address
        FROM appointments a
        LEFT JOIN users u ON a.client_id = u.user_id
        LEFT JOIN masters m ON a.master_id = m.id
        LEFT JOIN services s ON a.service_id = s.id
        WHERE a.status = 'active' 
        AND a.appointment_date = '2025-09-09'
    ''')
    appointments = cursor.fetchall()
    print(f"Записей с LEFT JOIN: {len(appointments)}")
    for app in appointments:
        print(f"Запись: мастер_id={app[2]}, время={app[5]}, статус={app[6]}")
    
    conn.close()

if __name__ == "__main__":
    check_users()
