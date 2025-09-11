#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с новыми мастерами
"""

import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database

def init_new_masters():
    """Инициализация базы данных с новыми мастерами"""
    
    # Создаем папку data если её нет
    os.makedirs("data", exist_ok=True)
    
    db = Database()
    
    print("Очистка старых данных...")
    
    # Очищаем старые данные
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments")
        cursor.execute("DELETE FROM services") 
        cursor.execute("DELETE FROM schedule")
        cursor.execute("DELETE FROM masters")
        cursor.execute("DELETE FROM users WHERE is_master = TRUE")
        conn.commit()
    
    print("Создание новых мастеров...")
    
    # Александра Мур - Аэрография
    master1_id = db.add_master(
        user_id=111111111,  # Замените на реальный user_id
        name="Александра Мур",
        specialization="Аэрография",
        social_media="https://t.me/Leader_rg",
        address="Студия аэрографии",
        password="alexandra123"
    )
    
    # Татьяна - Аэрография
    master2_id = db.add_master(
        user_id=222222222,  # Замените на реальный user_id
        name="Татьяна",
        specialization="Аэрография",
        social_media="https://t.me/tatyanaavoyan",
        address="Студия аэрографии",
        password="tatyana123"
    )
    
    # Анастасия - Аэрография
    master3_id = db.add_master(
        user_id=333333333,  # Замените на реальный user_id
        name="Анастасия",
        specialization="Аэрография",
        social_media="https://www.instagram.com/obmotka_aero_rg",
        address="Студия аэрографии",
        password="anastasia123"
    )
    
    # Мастер по татуировкам
    master4_id = db.add_master(
        user_id=444444444,  # Замените на реальный user_id
        name="Мастер по татуировкам",
        specialization="Татуировки",
        social_media="Студия художественной татуировки «Классик»",
        address="Студия художественной татуировки «Классик»",
        password="tattoo123"
    )
    
    print("Добавление услуг...")
    
    # Услуги Александры Мур - Аэрография булав
    db.add_service(master1_id, "Аэрография булав - 2 цвета БЕЗ рисунков", 2500, 120)
    db.add_service(master1_id, "Аэрография булав - 3+ цвета БЕЗ рисунков", 3000, 150)
    db.add_service(master1_id, "Аэрография булав - 2+ цвета + аппликации", 3500, 180)
    db.add_service(master1_id, "Аэрография булав - 2+ цвета + роспись краской", 4000, 200)
    
    # Услуги Александры Мур - Аэрография обруча
    db.add_service(master1_id, "Аэрография обруча - 2 цвета БЕЗ рисунков", 3000, 120)
    db.add_service(master1_id, "Аэрография обруча - 2+ цвета + аппликации", 3500, 150)
    db.add_service(master1_id, "Аэрография обруча - 2+ цвета + аппликация + роспись", 4000, 180)
    
    # Макет для аэрографии
    db.add_service(master1_id, "Макет для аэрографии обруча или булав", 500, 30)
    
    # Услуги Татьяны
    db.add_service(master2_id, "Любая аэрография", 4000, 180)
    
    # Услуги Анастасии
    db.add_service(master3_id, "Аэрография обруча/булав градиент", 3000, 120)
    db.add_service(master3_id, "Аэрография обруча/булав градиент + линии обмоткой", 3500, 150)
    db.add_service(master3_id, "Аэрография обруча/булав градиент + сложные узоры", 4500, 180)
    db.add_service(master3_id, "Сложная аэрография обруча/булав", 5000, 240)
    
    # Услуги мастера по татуировкам
    db.add_service(master4_id, "1 миниатюрная тату", 5000, 60)
    db.add_service(master4_id, "3 мини тату по акции", 10000, 180)
    db.add_service(master4_id, "Художественная татуировка", 5000, 120)
    db.add_service(master4_id, "Полный рабочий день", 25000, 480)
    db.add_service(master4_id, "Разработка эскиза", 1000, 60)
    db.add_service(master4_id, "Консультация мастера", 0, 30)
    
    print("Добавление расписания...")
    
    # Добавляем расписание на ближайшие дни
    from datetime import datetime, timedelta
    
    # Добавляем расписание на ближайшие 14 дней (чтобы покрыть рабочие дни)
    for i in range(1, 15):  # На 2 недели вперед
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Расписание для всех мастеров
        db.add_schedule(master1_id, date, "09:00", "18:00")
        db.add_schedule(master2_id, date, "10:00", "19:00")
        db.add_schedule(master3_id, date, "11:00", "20:00")
        db.add_schedule(master4_id, date, "12:00", "21:00")
    
    print("✅ База данных обновлена с новыми мастерами!")
    print("\nНовые мастера:")
    print("1. Александра Мур (Аэрография) - https://t.me/Leader_rg - Пароль: alexandra123")
    print("2. Татьяна (Аэрография) - https://t.me/tatyanaavoyan - Пароль: tatyana123")
    print("3. Анастасия (Аэрография) - https://www.instagram.com/obmotka_aero_rg - Пароль: anastasia123")
    print("4. Мастер по татуировкам (Татуировки) - Студия «Классик» - Пароль: tattoo123")
    print("\n⚠️  Не забудьте обновить user_id мастеров на реальные Telegram ID!")
    print(f"📁 База данных обновлена: {db.db_path}")

if __name__ == "__main__":
    init_new_masters()
