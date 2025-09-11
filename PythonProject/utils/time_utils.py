from datetime import datetime, timedelta, time
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class TimeUtils:
    """Утилиты для работы с временем и расписанием"""
    
    @staticmethod
    def generate_time_slots(start_time: str, end_time: str, duration: int = 60) -> List[str]:
        """
        Генерация временных слотов
        
        Args:
            start_time: Время начала в формате "HH:MM"
            end_time: Время окончания в формате "HH:MM"
            duration: Продолжительность слота в минутах
            
        Returns:
            Список временных слотов
        """
        slots = []
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        
        current = start
        while current + timedelta(minutes=duration) <= end:
            slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=duration)
        
        return slots
    
    @staticmethod
    def is_slot_available(slot_time: str, existing_appointments: List[Tuple], service_duration: int = 60) -> bool:
        """
        Проверка доступности временного слота
        
        Args:
            slot_time: Время слота в формате "HH:MM"
            existing_appointments: Список существующих записей
            service_duration: Продолжительность услуги в минутах
            
        Returns:
            True если слот доступен
        """
        slot_start = datetime.strptime(slot_time, "%H:%M").time()
        slot_end = (datetime.combine(datetime.today(), slot_start) + 
                   timedelta(minutes=service_duration)).time()
        
        logger.info(f"Проверка слота {slot_time} (продолжительность {service_duration} мин)")
        logger.info(f"Слот: {slot_start} - {slot_end}")
        
        for appointment in existing_appointments:
            if len(appointment) > 5:  # Проверяем что у нас есть время записи
                try:
                    app_time = datetime.strptime(appointment[5], "%H:%M").time()  # appointment_time
                    # Используем реальную продолжительность услуги из appointment[11] если доступна
                    app_duration = appointment[11] if len(appointment) > 11 else 60
                    app_end = (datetime.combine(datetime.today(), app_time) + 
                              timedelta(minutes=app_duration)).time()
                    
                    logger.info(f"Существующая запись: {app_time} - {app_end} (продолжительность {app_duration} мин)")
                    
                    # Проверка пересечения
                    if (slot_start < app_end and slot_end > app_time):
                        logger.info(f"❌ Слот {slot_time} пересекается с записью {app_time}")
                        return False
                    else:
                        logger.info(f"✅ Слот {slot_time} не пересекается с записью {app_time}")
                except (ValueError, IndexError) as e:
                    logger.error(f"Ошибка при обработке записи {appointment}: {e}")
                    continue
        
        logger.info(f"✅ Слот {slot_time} доступен")
        return True
    
    @staticmethod
    def format_date_russian(date_str: str) -> str:
        """
        Форматирование даты на русском языке
        
        Args:
            date_str: Дата в формате "YYYY-MM-DD"
            
        Returns:
            Отформатированная дата
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            months = [
                "января", "февраля", "марта", "апреля", "мая", "июня",
                "июля", "августа", "сентября", "октября", "ноября", "декабря"
            ]
            
            weekdays = [
                "понедельник", "вторник", "среда", "четверг", 
                "пятница", "суббота", "воскресенье"
            ]
            
            day = date_obj.day
            month = months[date_obj.month - 1]
            weekday = weekdays[date_obj.weekday()]
            
            return f"{day} {month} ({weekday})"
            
        except ValueError:
            return date_str
    
    @staticmethod
    def get_next_working_days(count: int = 7, skip_weekends: bool = False) -> List[Tuple[str, str]]:
        """
        Получение следующих рабочих дней
        
        Args:
            count: Количество дней
            skip_weekends: Пропускать выходные
            
        Returns:
            Список кортежей (дата в формате YYYY-MM-DD, отформатированная дата)
        """
        days = []
        current_date = datetime.now() + timedelta(days=1)  # Начинаем с завтра
        
        while len(days) < count:
            # Пропускаем выходные если нужно
            if skip_weekends and current_date.weekday() >= 5:  # 5 = суббота, 6 = воскресенье
                current_date += timedelta(days=1)
                continue
            
            date_str = current_date.strftime("%Y-%m-%d")
            formatted_date = TimeUtils.format_date_russian(date_str)
            
            days.append((date_str, formatted_date))
            current_date += timedelta(days=1)
        
        return days
    
    @staticmethod
    def is_time_in_past(date_str: str, time_str: str) -> bool:
        """
        Проверка, не находится ли время в прошлом
        
        Args:
            date_str: Дата в формате "YYYY-MM-DD"
            time_str: Время в формате "HH:MM"
            
        Returns:
            True если время в прошлом
        """
        try:
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            return appointment_datetime < datetime.now()
        except ValueError:
            return False
    
    @staticmethod
    def calculate_reminder_time(appointment_date: str, appointment_time: str, 
                              hours_before: int = 1) -> datetime:
        """
        Вычисление времени напоминания
        
        Args:
            appointment_date: Дата записи в формате "YYYY-MM-DD"
            appointment_time: Время записи в формате "HH:MM"
            hours_before: За сколько часов до записи отправить напоминание
            
        Returns:
            Время напоминания
        """
        try:
            appointment_datetime = datetime.strptime(
                f"{appointment_date} {appointment_time}", 
                "%Y-%m-%d %H:%M"
            )
            reminder_time = appointment_datetime - timedelta(hours=hours_before)
            return reminder_time
        except ValueError:
            logger.error(f"Invalid date/time format: {appointment_date} {appointment_time}")
            return None
    
    @staticmethod
    def get_week_schedule() -> List[Tuple[str, str]]:
        """
        Получение расписания на неделю
        
        Returns:
            Список дней недели с датами
        """
        schedule = []
        start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
        
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            date_str = current_day.strftime("%Y-%m-%d")
            formatted_date = TimeUtils.format_date_russian(date_str)
            
            schedule.append((date_str, formatted_date))
        
        return schedule
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """
        Форматирование продолжительности
        
        Args:
            minutes: Продолжительность в минутах
            
        Returns:
            Отформатированная строка
        """
        if minutes < 60:
            return f"{minutes} мин"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            
            if remaining_minutes == 0:
                return f"{hours} ч"
            else:
                return f"{hours} ч {remaining_minutes} мин"
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """
        Проверка формата времени
        
        Args:
            time_str: Строка времени
            
        Returns:
            True если формат корректный
        """
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        Проверка формата даты
        
        Args:
            date_str: Строка даты
            
        Returns:
            True если формат корректный
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
