#!/usr/bin/env python3
"""
Утилиты для администрирования бота
"""

from core.database import Database
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminUtils:
    def __init__(self):
        self.db = Database()
    
    def get_statistics(self):
        """Получение статистики"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM masters')
            total_masters = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "active"')
            active_appointments = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "completed"')
            completed_appointments = cursor.fetchone()[0]
            
            # Статистика за сегодня
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('SELECT COUNT(*) FROM appointments WHERE DATE(created_at) = ?', (today,))
            appointments_today = cursor.fetchone()[0]
            
            # Популярные услуги
            cursor.execute('''
                SELECT s.name, COUNT(*) as count
                FROM appointments a
                JOIN services s ON a.service_id = s.id
                WHERE a.status != 'cancelled'
                GROUP BY s.id
                ORDER BY count DESC
                LIMIT 5
            ''')
            popular_services = cursor.fetchall()
            
            return {
                'total_users': total_users,
                'total_masters': total_masters,
                'active_appointments': active_appointments,
                'completed_appointments': completed_appointments,
                'appointments_today': appointments_today,
                'popular_services': popular_services
            }
    
    def print_statistics(self):
        """Вывод статистики в консоль"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("         СТАТИСТИКА БОТА")
        print("="*50)
        print(f"👥 Всего пользователей: {stats['total_users']}")
        print(f"👨‍💼 Всего мастеров: {stats['total_masters']}")
        print(f"📅 Активные записи: {stats['active_appointments']}")
        print(f"✅ Завершенные записи: {stats['completed_appointments']}")
        print(f"📊 Записи сегодня: {stats['appointments_today']}")
        
        print("\n🏆 Популярные услуги:")
        for i, (service, count) in enumerate(stats['popular_services'], 1):
            print(f"{i}. {service}: {count} записей")
        
        print("="*50)
    
    def get_users_list(self):
        """Получение списка пользователей"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, first_name, is_master, created_at
                FROM users
                ORDER BY created_at DESC
            ''')
            return cursor.fetchall()
    
    def get_masters_list(self):
        """Получение списка мастеров"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.*, u.username, u.first_name
                FROM masters m
                JOIN users u ON m.user_id = u.user_id
                ORDER BY m.id
            ''')
            return cursor.fetchall()
    
    def get_recent_appointments(self, days=7):
        """Получение последних записей"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name as client_name, u.username,
                       m.name as master_name, s.name as service_name
                FROM appointments a
                JOIN users u ON a.client_id = u.user_id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE DATE(a.created_at) >= ?
                ORDER BY a.created_at DESC
            ''', (cutoff_date,))
            return cursor.fetchall()
    
    def cleanup_cancelled_appointments(self):
        """Очистка отмененных записей старше 30 дней"""
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM appointments 
                WHERE status = 'cancelled' AND DATE(created_at) < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
        
        print(f"🗑️ Удалено {deleted_count} старых отмененных записей")
    
    def backup_database(self, backup_path=None):
        """Создание резервной копии базы данных"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup_salon_bot_{timestamp}.db"
        
        import shutil
        try:
            # Создаем папку data если её нет
            os.makedirs("data", exist_ok=True)
            shutil.copy2(self.db.db_path, backup_path)
            print(f"✅ Резервная копия создана: {backup_path}")
        except Exception as e:
            print(f"❌ Ошибка создания резервной копии: {e}")
    
    def add_sample_master(self, name, specialization, social_media, address):
        """Добавление примерного мастера"""
        try:
            # Создаем фиктивный user_id
            import random
            user_id = random.randint(100000000, 999999999)
            
            # Добавляем пользователя
            self.db.add_user(user_id, f"master_{user_id}", name, is_master=True)
            
            # Добавляем мастера
            master_id = self.db.add_master(user_id, name, specialization, social_media, address)
            
            print(f"✅ Добавлен мастер: {name} (ID: {master_id})")
            return master_id
            
        except Exception as e:
            print(f"❌ Ошибка добавления мастера: {e}")
            return None

def main():
    """Главная функция для интерактивного управления"""
    admin = AdminUtils()
    
    while True:
        print("\n📊 АДМИН ПАНЕЛЬ")
        print("1. Показать статистику")
        print("2. Список пользователей")
        print("3. Список мастеров")
        print("4. Последние записи")
        print("5. Очистить старые записи")
        print("6. Создать резервную копию")
        print("7. Добавить примерного мастера")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            admin.print_statistics()
        
        elif choice == "2":
            users = admin.get_users_list()
            print(f"\n👥 Пользователи ({len(users)}):")
            for user in users[:10]:  # Показываем первые 10
                status = "👨‍💼 Мастер" if user[3] else "👤 Клиент"
                print(f"ID: {user[0]} | @{user[1] or 'N/A'} | {user[2]} | {status}")
        
        elif choice == "3":
            masters = admin.get_masters_list()
            print(f"\n👨‍💼 Мастера ({len(masters)}):")
            for master in masters:
                print(f"ID: {master[0]} | {master[2]} | {master[3]} | @{master[6] or 'N/A'}")
        
        elif choice == "4":
            appointments = admin.get_recent_appointments()
            print(f"\n📅 Последние записи ({len(appointments)}):")
            for app in appointments[:10]:  # Показываем первые 10
                print(f"{app[4]} {app[5]} | {app[7]} -> {app[9]} | {app[10]}")
        
        elif choice == "5":
            admin.cleanup_cancelled_appointments()
        
        elif choice == "6":
            admin.backup_database()
        
        elif choice == "7":
            print("\nДобавление мастера:")
            name = input("Имя: ")
            spec = input("Специализация: ")
            social = input("Соцсети: ")
            address = input("Адрес: ")
            
            master_id = admin.add_sample_master(name, spec, social, address)
            if master_id:
                # Добавляем несколько услуг
                services = [
                    ("Базовая услуга", 1000, 60),
                    ("Премиум услуга", 2000, 90)
                ]
                for service_name, price, duration in services:
                    admin.db.add_service(master_id, service_name, price, duration)
                print(f"Добавлены услуги для мастера {name}")
        
        elif choice == "0":
            print("До свидания!")
            break
        
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
