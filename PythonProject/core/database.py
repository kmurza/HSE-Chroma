import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Tuple

class Database:
    def __init__(self, db_path: str = "data/salon_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    is_master BOOLEAN DEFAULT FALSE,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица мастеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS masters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    name TEXT NOT NULL,
                    specialization TEXT,
                    social_media TEXT,
                    address TEXT,
                    password TEXT DEFAULT 'master123',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Таблица услуг
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_id INTEGER,
                    name TEXT NOT NULL,
                    price DECIMAL(10,2),
                    duration INTEGER, -- в минутах
                    FOREIGN KEY (master_id) REFERENCES masters (id)
                )
            ''')
            
            # Таблица расписания мастеров
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_id INTEGER,
                    date DATE,
                    start_time TIME,
                    end_time TIME,
                    is_available BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (master_id) REFERENCES masters (id)
                )
            ''')
            
            # Таблица записей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    master_id INTEGER,
                    service_id INTEGER,
                    appointment_date DATE,
                    appointment_time TIME,
                    status TEXT DEFAULT 'active', -- active, cancelled, completed
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES users (user_id),
                    FOREIGN KEY (master_id) REFERENCES masters (id),
                    FOREIGN KEY (service_id) REFERENCES services (id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str, first_name: str, is_master: bool = False, phone: str = None):
        """Добавление пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, is_master, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, is_master, phone))
            conn.commit()
    
    def get_user(self, user_id: int):
        """Получение информации о пользователе"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def is_master(self, user_id: int) -> bool:
        """Проверка, является ли пользователь мастером"""
        user = self.get_user(user_id)
        return user and user[3]  # is_master field
    
    def add_master(self, user_id: int, name: str, specialization: str, social_media: str, address: str, password: str = 'master123'):
        """Добавление мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO masters (user_id, name, specialization, social_media, address, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, specialization, social_media, address, password))
            
            # Обновляем статус пользователя
            cursor.execute('UPDATE users SET is_master = TRUE WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.lastrowid
    
    def update_master_user_id(self, master_id: int, new_user_id: int):
        """Обновление user_id мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE masters SET user_id = ? WHERE id = ?', (new_user_id, master_id))
            cursor.execute('UPDATE users SET is_master = TRUE WHERE user_id = ?', (new_user_id,))
            conn.commit()
    
    def get_masters(self):
        """Получение списка всех мастеров"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM masters')
            return cursor.fetchall()
    
    def get_masters_by_specialization(self, specialization: str):
        """Получение мастеров по специализации"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM masters WHERE specialization = ?', (specialization,))
            return cursor.fetchall()
    
    def get_master_by_user_id(self, user_id: int):
        """Получение мастера по user_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM masters WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    
    def get_master_by_name_and_password(self, name: str, password: str):
        """Получение мастера по имени и паролю"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM masters WHERE name = ? AND password = ?', (name, password))
            return cursor.fetchone()
    
    def get_masters_list(self):
        """Получение списка всех мастеров для выбора"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, specialization FROM masters ORDER BY name')
            return cursor.fetchall()
    
    def add_service(self, master_id: int, name: str, price: float, duration: int):
        """Добавление услуги"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services (master_id, name, price, duration)
                VALUES (?, ?, ?, ?)
            ''', (master_id, name, price, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_services_by_master(self, master_id: int):
        """Получение услуг мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM services WHERE master_id = ?', (master_id,))
            return cursor.fetchall()
    
    def add_schedule(self, master_id: int, date: str, start_time: str, end_time: str):
        """Добавление расписания"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO schedule (master_id, date, start_time, end_time)
                VALUES (?, ?, ?, ?)
            ''', (master_id, date, start_time, end_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_available_schedule(self, master_id: int, date: str):
        """Получение доступного расписания мастера на дату"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM schedule 
                WHERE master_id = ? AND date = ? AND is_available = TRUE
            ''', (master_id, date))
            return cursor.fetchall()
    
    def is_time_available(self, master_id: int, appointment_date: str, appointment_time: str):
        """Проверка доступности времени у мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE master_id = ? AND appointment_date = ? AND appointment_time = ? AND status = 'active'
            ''', (master_id, appointment_date, appointment_time))
            count = cursor.fetchone()[0]
            return count == 0
    
    def create_appointment(self, client_id: int, master_id: int, service_id: int, 
                          appointment_date: str, appointment_time: str):
        """Создание записи"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO appointments (client_id, master_id, service_id, appointment_date, appointment_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, master_id, service_id, appointment_date, appointment_time))
            conn.commit()
            return cursor.lastrowid
    
    def get_client_appointments(self, client_id: int):
        """Получение записей клиента"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, a.client_id, a.master_id, a.service_id, 
                       a.appointment_date, a.appointment_time, a.status, a.created_at,
                       m.name as master_name, s.name as service_name, s.price, s.duration
                FROM appointments a
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.client_id = ? AND a.status = 'active'
                ORDER BY a.appointment_date, a.appointment_time
            ''', (client_id,))
            return cursor.fetchall()
    
    def get_master_appointments(self, master_id: int):
        """Получение записей мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, u.username, s.name as service_name
                FROM appointments a
                JOIN users u ON a.client_id = u.user_id
                JOIN services s ON a.service_id = s.id
                WHERE a.master_id = ? AND a.status = 'active'
                ORDER BY a.appointment_date, a.appointment_time
            ''', (master_id,))
            return cursor.fetchall()
    
    def cancel_appointment(self, appointment_id: int):
        """Отмена записи"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE appointments SET status = 'cancelled' WHERE id = ?
            ''', (appointment_id,))
            conn.commit()
    
    def get_appointments_for_reminder(self):
        """Получение записей для напоминаний (на завтра)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, m.name as master_name, s.name as service_name
                FROM appointments a
                JOIN users u ON a.client_id = u.user_id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.status = 'active' 
                AND date(a.appointment_date) = date('now', '+1 day')
            ''')
            return cursor.fetchall()
    
    def get_appointments_by_time(self, date: str, time: str):
        """Получение записей на определенное время"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, m.name as master_name, s.name as service_name, m.address
                FROM appointments a
                JOIN users u ON a.client_id = u.user_id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.status = 'active' 
                AND a.appointment_date = ? 
                AND a.appointment_time = ?
            ''', (date, time))
            return cursor.fetchall()
    
    def get_appointments_by_date(self, date: str):
        """Получение всех записей на определенную дату"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, m.name as master_name, s.name as service_name, s.duration, m.address
                FROM appointments a
                LEFT JOIN users u ON a.client_id = u.user_id
                LEFT JOIN masters m ON a.master_id = m.id
                LEFT JOIN services s ON a.service_id = s.id
                WHERE a.status = 'active' 
                AND a.appointment_date = ?
            ''', (date,))
            return cursor.fetchall()
    
    def get_appointment_by_id(self, appointment_id: int):
        """Получение записи по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.first_name, m.name as master_name, s.name as service_name
                FROM appointments a
                JOIN users u ON a.client_id = u.user_id
                JOIN masters m ON a.master_id = m.id
                JOIN services s ON a.service_id = s.id
                WHERE a.id = ?
            ''', (appointment_id,))
            return cursor.fetchone()
    
    def get_master_schedule(self, master_id: int):
        """Получение расписания мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM schedule WHERE master_id = ? ORDER BY date, start_time
            ''', (master_id,))
            return cursor.fetchall()
    
    def delete_schedule_by_id(self, schedule_id: int):
        """Удаление конкретного расписания по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM schedule WHERE id = ?', (schedule_id,))
            conn.commit()
    
    def delete_master_schedule(self, master_id: int):
        """Удаление всего расписания мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM schedule WHERE master_id = ?', (master_id,))
            conn.commit()
    
    def delete_service_by_id(self, service_id: int):
        """Удаление конкретной услуги по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
            conn.commit()
    
    def delete_master_services(self, master_id: int):
        """Удаление всех услуг мастера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM services WHERE master_id = ?', (master_id,))
            conn.commit()
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path)
