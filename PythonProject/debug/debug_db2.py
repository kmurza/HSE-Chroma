#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import Database

def test_get_appointments():
    db = Database()
    
    print("=== ТЕСТ get_appointments_by_date ===")
    appointments = db.get_appointments_by_date("2025-09-09")
    
    print(f"Найдено записей: {len(appointments)}")
    for app in appointments:
        print(f"Запись: мастер_id={app[2]}, время={app[5]}, статус={app[6]}")
    
    print("\n=== ФИЛЬТРАЦИЯ ПО МАСТЕРУ 21 ===")
    filtered = [app for app in appointments if app[2] == 21]
    print(f"Записей к мастеру 21: {len(filtered)}")
    for app in filtered:
        print(f"Запись: время={app[5]}, статус={app[6]}")

if __name__ == "__main__":
    test_get_appointments()
