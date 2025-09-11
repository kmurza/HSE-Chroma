#!/usr/bin/env python3
import sqlite3

def check_appointments():
    conn = sqlite3.connect('data/salon_bot.db')
    cursor = conn.cursor()
    
    print("=== ВСЕ ЗАПИСИ НА 9 СЕНТЯБРЯ ===")
    cursor.execute('SELECT * FROM appointments WHERE appointment_date = "2025-09-09"')
    appointments = cursor.fetchall()
    
    for app in appointments:
        print(f"ID: {app[0]}, Client: {app[1]}, Master: {app[2]}, Service: {app[3]}, Date: {app[4]}, Time: {app[5]}, Status: {app[6]}")
    
    print(f"\nВсего записей на 9 сентября: {len(appointments)}")
    
    print("\n=== ЗАПИСИ НА 9 СЕНТЯБРЯ В 09:00 ===")
    cursor.execute('SELECT * FROM appointments WHERE appointment_date = "2025-09-09" AND appointment_time = "09:00"')
    appointments_9am = cursor.fetchall()
    
    for app in appointments_9am:
        print(f"ID: {app[0]}, Client: {app[1]}, Master: {app[2]}, Service: {app[3]}, Date: {app[4]}, Time: {app[5]}, Status: {app[6]}")
    
    print(f"\nЗаписей на 9 сентября в 09:00: {len(appointments_9am)}")
    
    conn.close()

if __name__ == "__main__":
    check_appointments()
