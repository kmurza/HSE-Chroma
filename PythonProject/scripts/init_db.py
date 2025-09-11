#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с примерными данными
"""

import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database

def init_sample_data():
    """Инициализация базы данных с примерными данными"""
    
    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)
    
    db = Database()
    
    print("Создание примерных мастеров...")
    
    # Добавляем примерных мастеров (используем фиктивные user_id)
    master1_id = db.add_master(
        user_id=111111111,  # Замените на реальный user_id
        name="Анна Иванова",
        specialization="Парикмахер",
        social_media="@anna_hair",
        address="ул. Пушкина, 10"
    )
    
    master2_id = db.add_master(
        user_id=222222222,  # Замените на реальный user_id
        name="Елена Петрова",
        specialization="Маникюр/Педикюр",
        social_media="@elena_nails",
        address="ул. Ленина, 25"
    )
    
    master3_id = db.add_master(
        user_id=333333333,  # Замените на реальный user_id
        name="Мария Сидорова",
        specialization="Косметолог",
        social_media="@maria_beauty",
        address="пр. Мира, 15"
    )
    
    print("Добавление услуг...")
    
    # Услуги для парикмахера
    db.add_service(master1_id, "Стрижка мужская", 1500, 60)
    db.add_service(master1_id, "Стрижка женская", 2000, 90)
    db.add_service(master1_id, "Окрашивание", 3500, 180)
    db.add_service(master1_id, "Укладка", 1200, 45)
    
    # Услуги для мастера маникюра
    db.add_service(master2_id, "Маникюр классический", 1000, 90)
    db.add_service(master2_id, "Маникюр аппаратный", 1200, 90)
    db.add_service(master2_id, "Педикюр", 1500, 120)
    db.add_service(master2_id, "Наращивание ногтей", 2500, 150)
    
    # Услуги для косметолога
    db.add_service(master3_id, "Чистка лица", 2000, 90)
    db.add_service(master3_id, "Пилинг", 2500, 60)
    db.add_service(master3_id, "Массаж лица", 1800, 60)
    db.add_service(master3_id, "Уход за кожей", 3000, 120)
    
    print("Добавление расписания...")
    
    # Добавляем расписание на ближайшие дни
    from datetime import datetime, timedelta
    
    for i in range(1, 8):  # На неделю вперед
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Расписание для всех мастеров
        db.add_schedule(master1_id, date, "09:00", "18:00")
        db.add_schedule(master2_id, date, "10:00", "19:00")
        db.add_schedule(master3_id, date, "11:00", "20:00")
    
    print("✅ База данных инициализирована с примерными данными!")
    print("\nПримерные мастера:")
    print("1. Анна Иванова (Парикмахер) - @anna_hair")
    print("2. Елена Петрова (Маникюр/Педикюр) - @elena_nails")
    print("3. Мария Сидорова (Косметолог) - @maria_beauty")
    print("\n⚠️  Не забудьте обновить user_id мастеров на реальные Telegram ID!")
    print(f"📁 База данных создана: {db.db_path}")

if __name__ == "__main__":
    init_sample_data()
