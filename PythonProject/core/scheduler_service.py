import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import Database
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    """Сервис для работы с планировщиком и напоминаниями"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = Database()
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Запуск планировщика"""
        # Напоминания за день до записи в 10:00
        self.scheduler.add_job(
            self.send_daily_reminders,
            'cron',
            hour=10,
            minute=0,
            id='daily_reminders'
        )
        
        # Напоминания за час до записи (каждые 15 минут для точности)
        self.scheduler.add_job(
            self.send_hourly_reminders,
            'cron',
            minute='0,15,30,45',  # Каждые 15 минут
            id='hourly_reminders'
        )
        
        # Очистка старых записей в полночь
        self.scheduler.add_job(
            self.cleanup_old_appointments,
            'cron',
            hour=0,
            minute=0,
            id='cleanup'
        )
        
        self.scheduler.start()
        logger.info("⏰ Scheduler started")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("⏰ Scheduler stopped")
    
    async def send_daily_reminders(self):
        """Отправка напоминаний за день до записи"""
        try:
            appointments = self.db.get_appointments_for_reminder()
            
            for app in appointments:
                try:
                    text = (
                        f"🔔 Напоминание!\n\n"
                        f"У вас завтра запись:\n"
                        f"📅 {datetime.strptime(app[4], '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
                        f"⏰ {app[5]}\n"
                        f"👨‍💼 Мастер: {app[7]}\n"
                        f"💇‍♀️ Услуга: {app[8]}\n\n"
                        f"Не забудьте про вашу запись! 😊"
                    )
                    
                    await self.bot.send_message(chat_id=app[1], text=text)
                    logger.info(f"Daily reminder sent to user {app[1]}")
                    
                except Exception as e:
                    logger.error(f"Failed to send daily reminder to user {app[1]}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in send_daily_reminders: {e}")
    
    async def send_hourly_reminders(self):
        """Отправка напоминаний за час до записи"""
        try:
            current_time = datetime.now()
            # Проверяем записи в ближайшие 45-75 минут (чтобы поймать час)
            for minutes_ahead in range(45, 76, 15):  # 45, 60, 75 минут
                target_datetime = current_time + timedelta(minutes=minutes_ahead)
                target_date = target_datetime.strftime("%Y-%m-%d")
                target_time = target_datetime.strftime("%H:%M")
                
                # Получаем все записи на сегодня
                appointments = self.db.get_appointments_by_date(target_date)
                
                for app in appointments:
                    try:
                        # Проверяем, точно ли это за час до записи
                        app_datetime = datetime.strptime(f"{app[4]} {app[5]}", "%Y-%m-%d %H:%M")
                        time_diff = app_datetime - current_time
                        
                        # Если до записи осталось от 55 до 65 минут - отправляем напоминание
                        if timedelta(minutes=55) <= time_diff <= timedelta(minutes=65):
                            # Проверяем, не отправляли ли уже напоминание
                            if not hasattr(app, '_reminder_sent'):
                                text = (
                                    f"⏰ Напоминание!\n\n"
                                    f"Ваша запись через час:\n"
                                    f"📅 {target_date}\n"
                                    f"⏰ {app[5]}\n"
                                    f"👨‍💼 Мастер: {app[7]}\n"
                                    f"💇‍♀️ Услуга: {app[8]}\n"
                                    f"📍 Адрес: {app[9]}\n\n"
                                    f"Подготовьтесь к визиту! 🎯"
                                )
                                
                                await self.bot.send_message(chat_id=app[1], text=text)
                                logger.info(f"Hourly reminder sent to user {app[1]} for appointment at {app[5]}")
                                
                    except Exception as e:
                        logger.error(f"Failed to send hourly reminder to user {app[1]}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in send_hourly_reminders: {e}")
    
    async def cleanup_old_appointments(self):
        """Очистка старых записей"""
        try:
            # Помечаем как завершенные записи старше 1 дня
            cutoff_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE appointments 
                    SET status = 'completed' 
                    WHERE appointment_date < ? AND status = 'active'
                ''', (cutoff_date,))
                
                updated_count = cursor.rowcount
                conn.commit()
                
            logger.info(f"🧹 Cleaned up {updated_count} old appointments")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_appointments: {e}")
    
    def add_custom_reminder(self, appointment_id: int, reminder_time: datetime):
        """Добавление кастомного напоминания"""
        job_id = f"reminder_{appointment_id}"
        
        self.scheduler.add_job(
            self.send_custom_reminder,
            'date',
            run_date=reminder_time,
            args=[appointment_id],
            id=job_id
        )
        
        logger.info(f"Custom reminder scheduled for appointment {appointment_id} at {reminder_time}")
    
    async def send_custom_reminder(self, appointment_id: int):
        """Отправка кастомного напоминания"""
        try:
            appointment = self.db.get_appointment_by_id(appointment_id)
            
            if not appointment or appointment[7] != 'active':  # status
                return
            
            text = (
                f"🔔 Напоминание о записи!\n\n"
                f"📅 {datetime.strptime(appointment[4], '%Y-%m-%d').strftime('%d.%m.%Y')}\n"
                f"⏰ {appointment[5]}\n"
                f"👨‍💼 Мастер: {appointment[8]}\n"
                f"💇‍♀️ Услуга: {appointment[9]}"
            )
            
            await self.bot.send_message(chat_id=appointment[1], text=text)
            
        except Exception as e:
            logger.error(f"Failed to send custom reminder for appointment {appointment_id}: {e}")
