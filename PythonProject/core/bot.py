import logging
from datetime import datetime, timedelta
import telebot
from telebot import types
from core.database import Database
from config.settings import BOT_TOKEN, MESSAGES, KEYBOARDS, MASTER_PASSWORD
from utils.time_utils import TimeUtils

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SalonBot:
    def __init__(self):
        self.db = Database()
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.user_data = {}  # Храним данные пользователей
        self._processed_callbacks = set()  # Для отслеживания обработанных callback'ов
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            self.start(message)
        
        @self.bot.message_handler(commands=['menu'])
        def menu_handler(message):
            self.show_main_menu(message)
        
        @self.bot.message_handler(func=lambda message: True)
        def message_handler(message):
            self.handle_message(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            self.handle_callback(call)
    
    def start(self, message):
        """Обработчик команды /start"""
        user = message.from_user
        
        # Добавляем пользователя в базу
        self.db.add_user(user.id, user.username, user.first_name)
        
        # Создаем клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for row in KEYBOARDS['main_menu']:
            markup.row(*row)
        
        self.bot.send_message(message.chat.id, MESSAGES['welcome'], reply_markup=markup)
    
    def show_main_menu(self, message):
        """Показать главное меню"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for row in KEYBOARDS['main_menu']:
            markup.row(*row)
        
        self.bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    
    def handle_message(self, message):
        """Обработчик текстовых сообщений"""
        text = message.text
        user_id = message.from_user.id
        
        # Защита от дублирования сообщений
        message_key = f"{user_id}_{message.message_id}"
        if hasattr(self, '_processed_messages'):
            if message_key in self._processed_messages:
                logger.warning(f"Дублированное сообщение: {message_key}")
                return
            self._processed_messages.add(message_key)
            # Очищаем старые сообщения (оставляем только последние 1000)
            if len(self._processed_messages) > 1000:
                self._processed_messages.clear()
        else:
            self._processed_messages = {message_key}
        
        # Проверяем, ожидает ли пользователь ввода пароля мастера
        if user_id in self.user_data and self.user_data[user_id].get('waiting_for_master_password'):
            # Если пользователь нажимает кнопки меню - выходим из режима ввода пароля
            if text in ["📅 Записаться", "📋 Мои записи", "❌ Отменить запись", "👨‍💼 Режим мастера", "👤 Режим клиента"]:
                self.user_data[user_id]['waiting_for_master_password'] = False
                # Обрабатываем нажатую кнопку
                if text == "📅 Записаться":
                    self.show_service_types(message)
                elif text == "📋 Мои записи":
                    self.show_my_appointments(message)
                elif text == "❌ Отменить запись":
                    self.show_appointments_to_cancel(message)
                elif text == "👨‍💼 Режим мастера":
                    self.request_master_password(message)
                elif text == "👤 Режим клиента":
                    self.client_mode(message)
                return
            # Если пользователь хочет выйти из режима ввода пароля
            if text in ["🏠 Главное меню", "/menu", "меню", "выход", "отмена"]:
                self.user_data[user_id]['waiting_for_master_password'] = False
                self.show_main_menu(message)
                return
            self.handle_master_login_password(message, text)
            return
        
        # Обработка специальных команд
        if text.startswith("МАСТЕР:"):
            self.process_master_registration(message, text)
            return
        elif text.startswith("РАСПИСАНИЕ:"):
            # Проверяем, что пользователь вошел под мастером
            if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
                self.bot.send_message(message.chat.id, "❌ Только мастера могут добавлять расписание.")
                return
            self.process_schedule_addition(message, text)
            return
        elif text.startswith("УСЛУГА:"):
            # Проверяем, что пользователь вошел под мастером
            if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
                self.bot.send_message(message.chat.id, "❌ Только мастера могут добавлять услуги.")
                return
            self.process_service_addition(message, text)
            return
        
        # Обработка кнопок меню
        if text == "📅 Записаться":
            self.show_service_types(message)
        elif text == "📋 Мои записи":
            self.show_my_appointments(message)
        elif text == "❌ Отменить запись":
            self.show_appointments_to_cancel(message)
        elif text == "👨‍💼 Режим мастера":
            self.request_master_password(message)
        elif text == "👤 Режим клиента":
            self.client_mode(message)
        elif text == "📅 Добавить расписание":
            self.add_schedule_start(message)
        elif text == "👥 Мои клиенты":
            self.show_master_appointments(message)
        elif text == "💇‍♀️ Добавить услугу":
            self.add_service_start(message)
        elif text == "📋 Просмотр расписания":
            self.show_master_schedule(message)
        elif text == "🗑️ Удалить расписание":
            self.delete_schedule_start(message)
        elif text == "🗑️ Удалить услугу":
            self.delete_service_start(message)
        elif text == "🔙 Назад в меню":
            if self.db.is_master(user_id):
                self.master_mode(message)
            else:
                self.show_main_menu(message)
        else:
            self.bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки меню.")
    
    def show_service_types(self, message):
        """Показать типы услуг"""
        # Получаем уникальные специализации мастеров
        masters = self.db.get_masters()
        
        if not masters:
            self.bot.send_message(message.chat.id, "Пока нет доступных мастеров.")
            return
        
        # Создаем уникальный список специализаций
        specializations = list(set([master[3] for master in masters if master[3]]))
        
        if not specializations:
            self.bot.send_message(message.chat.id, "Нет доступных типов услуг.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for specialization in sorted(specializations):
            button = types.InlineKeyboardButton(
                specialization,
                callback_data=f"specialization_{specialization}"
            )
            markup.add(button)
        
        self.bot.send_message(message.chat.id, MESSAGES['choose_service'], reply_markup=markup)
    
    def show_masters_by_specialization(self, call, specialization):
        """Показать мастеров по выбранной специализации"""
        masters = self.db.get_masters_by_specialization(specialization)
        
        if not masters:
            self.bot.edit_message_text(
                f"Нет доступных мастеров по специализации '{specialization}'.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for master in masters:
            button = types.InlineKeyboardButton(
                f"{master[2]} - {master[5]}",  # name - address
                callback_data=f"master_{master[0]}"
            )
            markup.add(button)
        
        if call.from_user.id not in self.user_data:
            self.user_data[call.from_user.id] = {}
        self.user_data[call.from_user.id]['selected_specialization'] = specialization
        
        self.bot.edit_message_text(
            MESSAGES['choose_master'],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def show_my_appointments(self, message):
        """Показать записи клиента"""
        user_id = message.from_user.id
        appointments = self.db.get_client_appointments(user_id)
        
        if not appointments:
            self.bot.send_message(message.chat.id, MESSAGES['no_appointments'])
            return
        
        text = "📋 Ваши записи:\n\n"
        for app in appointments:
            formatted_date = TimeUtils.format_date_russian(app[4])  # appointment_date
            duration_str = TimeUtils.format_duration(app[11])  # duration
            text += f"📅 {formatted_date} в {app[5]}\n"  # appointment_time
            text += f"👨‍💼 Мастер: {app[8]}\n"  # master_name
            text += f"💇‍♀️ Услуга: {app[9]}\n"  # service_name
            text += f"💰 Цена: {app[10]} руб.\n"  # price
            text += f"⏳ Продолжительность: {duration_str}\n\n"  # duration
        
        self.bot.send_message(message.chat.id, text)
    
    def show_appointments_to_cancel(self, message):
        """Показать записи для отмены"""
        user_id = message.from_user.id
        appointments = self.db.get_client_appointments(user_id)
        
        if not appointments:
            self.bot.send_message(message.chat.id, MESSAGES['no_appointments'])
            return
        
        markup = types.InlineKeyboardMarkup()
        for app in appointments:
            formatted_date = TimeUtils.format_date_russian(app[4])  # appointment_date
            button_text = f"{formatted_date} {app[5]} - {app[8]}"  # appointment_time, master_name
            button = types.InlineKeyboardButton(button_text, callback_data=f"cancel_{app[0]}")
            markup.add(button)
        
        self.bot.send_message(message.chat.id, "Выберите запись для отмены:", reply_markup=markup)
    
    def request_master_password(self, message):
        """Запрос пароля для входа в режим мастера"""
        user_id = message.from_user.id
        
        # Инициализируем данные пользователя если их нет
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        
        # Показываем меню выбора: войти как существующий мастер или создать нового
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔑 Войти как существующий мастер", callback_data="login_existing_master"))
        markup.add(types.InlineKeyboardButton("➕ Создать нового мастера", callback_data="create_new_master"))
        
        self.bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    
    def handle_master_login_password(self, message, password):
        """Обработка введенного пароля для входа под мастером"""
        user_id = message.from_user.id
        master_id = self.user_data[user_id].get('selected_master_for_login')
        
        if not master_id:
            self.bot.send_message(message.chat.id, "Ошибка: мастер не выбран.")
            return
        
        # Получаем мастера по ID
        masters = self.db.get_masters()
        master = next((m for m in masters if m[0] == master_id), None)
        
        if not master:
            self.bot.send_message(message.chat.id, "Ошибка: мастер не найден.")
            return
        
        # Проверяем пароль
        if password == master[6]:  # password field
            # Пароль верный - входим под мастером
            
            # Если у мастера фиктивный user_id, обновляем его на реальный
            if master[1] == 111111111:  # фиктивный user_id
                self.db.update_master_user_id(master_id, user_id)
            
            self.user_data[user_id]['waiting_for_master_password'] = False
            self.user_data[user_id]['current_master_id'] = master_id
            self.user_data[user_id]['current_master_name'] = master[2]
            
            self.bot.send_message(message.chat.id, f"✅ Успешный вход под мастером '{master[2]}'!")
            self.show_master_menu(message)
        else:
            # Неверный пароль
            self.bot.send_message(message.chat.id, "❌ Неверный пароль! Попробуйте еще раз.")
    
    def show_master_menu(self, message):
        """Показать меню мастера"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for row in KEYBOARDS['master_menu']:
            markup.row(*row)
        
        self.bot.send_message(message.chat.id, MESSAGES['master_menu'], reply_markup=markup)
    
    def client_mode(self, message):
        """Переключение в режим клиента"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for row in KEYBOARDS['main_menu']:
            markup.row(*row)
        
        self.bot.send_message(message.chat.id, "Режим клиента активирован", reply_markup=markup)
    
    def add_schedule_start(self, message):
        """Начало добавления расписания с динамическими кнопками"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "❌ Вы не вошли под мастером.")
            return
        
        # Получаем доступные даты для выбора
        days = TimeUtils.get_next_working_days(count=14, skip_weekends=False)
        
        markup = types.InlineKeyboardMarkup()
        for date_str, formatted_date in days:
            button = types.InlineKeyboardButton(formatted_date, callback_data=f"add_sched_date_{date_str}")
            markup.add(button)
        
        self.bot.send_message(
            message.chat.id,
            "📅 Добавление расписания\n\nВыберите дату для добавления рабочего времени:",
            reply_markup=markup
        )
    
    def add_schedule_select_start_time(self, call, date):
        """Выбор времени начала работы"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "❌ Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Сохраняем выбранную дату
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['schedule_date'] = date
        
        # Генерируем временные слоты для начала работы (с 6:00 до 12:00)
        time_slots = TimeUtils.generate_time_slots("06:00", "12:00", 30)  # каждые 30 минут
        
        markup = types.InlineKeyboardMarkup()
        for time_slot in time_slots:
            button = types.InlineKeyboardButton(time_slot, callback_data=f"add_sched_start_{time_slot}")
            markup.add(button)
        
        formatted_date = TimeUtils.format_date_russian(date)
        self.bot.edit_message_text(
            f"📅 {formatted_date}\n\n⏰ Выберите время начала работы:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def add_schedule_select_end_time(self, call, start_time):
        """Выбор времени окончания работы"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "❌ Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Сохраняем время начала
        self.user_data[user_id]['schedule_start_time'] = start_time
        
        # Вычисляем минимальное время окончания (начало + 2 часа)
        try:
            start_datetime = datetime.strptime(start_time, "%H:%M")
            min_end_datetime = start_datetime + timedelta(hours=2)
            min_end_time = min_end_datetime.strftime("%H:%M")
            
            # Генерируем слоты с минимального времени до 22:00
            end_hour = max(min_end_datetime.hour, 10)  # не раньше 10:00
            end_time_str = f"{end_hour:02d}:00"
            
            time_slots = TimeUtils.generate_time_slots(end_time_str, "22:00", 30)
            
            markup = types.InlineKeyboardMarkup()
            for time_slot in time_slots:
                if time_slot > start_time:  # только время после начала работы
                    button = types.InlineKeyboardButton(time_slot, callback_data=f"add_sched_end_{time_slot}")
                    markup.add(button)
            
            date = self.user_data[user_id].get('schedule_date', '')
            formatted_date = TimeUtils.format_date_russian(date)
            
            self.bot.edit_message_text(
                f"📅 {formatted_date}\n⏰ Начало: {start_time}\n\nВыберите время окончания работы:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
            
        except Exception as e:
            self.bot.edit_message_text(
                "❌ Ошибка при выборе времени. Попробуйте снова.",
                call.message.chat.id,
                call.message.message_id
            )
    
    def add_schedule_confirm(self, call, end_time):
        """Подтверждение и добавление расписания"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "❌ Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        try:
            master_id = self.user_data[user_id]['current_master_id']
            date = self.user_data[user_id]['schedule_date']
            start_time = self.user_data[user_id]['schedule_start_time']
            
            # Добавляем расписание в базу данных
            self.db.add_schedule(master_id, date, start_time, end_time)
            
            formatted_date = TimeUtils.format_date_russian(date)
            
            self.bot.edit_message_text(
                f"✅ Расписание успешно добавлено!\n\n"
                f"📅 {formatted_date}\n"
                f"⏰ {start_time} - {end_time}",
                call.message.chat.id,
                call.message.message_id
            )
            
            # Очищаем временные данные
            if 'schedule_date' in self.user_data[user_id]:
                del self.user_data[user_id]['schedule_date']
            if 'schedule_start_time' in self.user_data[user_id]:
                del self.user_data[user_id]['schedule_start_time']
                
        except Exception as e:
            self.bot.edit_message_text(
                f"❌ Ошибка при добавлении расписания: {str(e)}",
                call.message.chat.id,
                call.message.message_id
            )
    
    def add_service_start(self, message):
        """Начало добавления услуги"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "❌ Вы не вошли под мастером.")
            return
        
        self.bot.send_message(
            message.chat.id,
            "💇‍♀️ Добавление услуги\n\n"
            "Отправьте данные в формате:\n"
            "УСЛУГА: Название | Цена | Продолжительность(мин)\n\n"
            "Например:\n"
            "УСЛУГА: Стрижка мужская | 1500 | 60"
        )
    
    def show_master_appointments(self, message):
        """Показать записи мастера"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "Вы не вошли под мастером.")
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        appointments = self.db.get_master_appointments(master_id)
        
        if not appointments:
            self.bot.send_message(message.chat.id, "У вас нет записей.")
            return
        
        text = "👥 Ваши клиенты:\n\n"
        for app in appointments:
            formatted_date = TimeUtils.format_date_russian(app[4])  # appointment_date
            text += f"📅 {formatted_date} в {app[5]}\n"  # appointment_time
            text += f"👤 Клиент: {app[8]} (@{app[9] or 'без username'})\n"  # first_name, username
            text += f"💇‍♀️ Услуга: {app[10]}\n\n"  # service_name
        
        self.bot.send_message(message.chat.id, text)
    
    def handle_callback(self, call):
        """Обработчик callback запросов"""
        self.bot.answer_callback_query(call.id)
        
        data = call.data
        
        # Защита от дублирования - проверяем, не обрабатывали ли мы уже этот callback
        callback_key = f"{call.from_user.id}_{call.id}"
        if callback_key in self._processed_callbacks:
            logger.warning(f"Дублированный callback: {callback_key}")
            return
        self._processed_callbacks.add(callback_key)
        
        # Очищаем старые callback'и (оставляем только последние 1000)
        if len(self._processed_callbacks) > 1000:
            self._processed_callbacks.clear()
        
        if data.startswith("specialization_"):
            specialization = data.split("_", 1)[1]
            self.show_masters_by_specialization(call, specialization)
        elif data.startswith("master_"):
            master_id = int(data.split("_")[1])
            self.show_master_info(call, master_id)
        elif data.startswith("service_"):
            service_id = int(data.split("_")[1])
            if call.from_user.id not in self.user_data:
                self.user_data[call.from_user.id] = {}
            self.user_data[call.from_user.id]['selected_service'] = service_id
            self.show_available_dates(call)
        elif data.startswith("date_"):
            date = data.split("_")[1]
            if call.from_user.id not in self.user_data:
                self.user_data[call.from_user.id] = {}
            self.user_data[call.from_user.id]['selected_date'] = date
            self.show_available_times(call)
        elif data.startswith("time_"):
            time = data.split("_")[1]
            self.create_appointment(call, time)
        elif data.startswith("cancel_"):
            appointment_id = int(data.split("_")[1])
            self.cancel_appointment(call, appointment_id)
        elif data == "login_existing_master":
            self.show_masters_for_login(call)
        elif data == "create_new_master":
            self.start_master_registration(call)
        elif data.startswith("login_master_"):
            master_id = int(data.split("_")[2])
            self.request_master_login_password(call, master_id)
        elif data.startswith("delete_schedule_"):
            schedule_id = int(data.split("_")[2])
            self.delete_specific_schedule(call, schedule_id)
        elif data == "delete_all_schedule":
            self.delete_all_schedule(call)
        elif data.startswith("delete_service_"):
            service_id = int(data.split("_")[2])
            self.delete_specific_service(call, service_id)
        elif data == "delete_all_services":
            self.delete_all_services(call)
        elif data.startswith("add_sched_date_"):
            date = data.split("_")[3]
            self.add_schedule_select_start_time(call, date)
        elif data.startswith("add_sched_start_"):
            start_time = data.split("_")[3]
            self.add_schedule_select_end_time(call, start_time)
        elif data.startswith("add_sched_end_"):
            end_time = data.split("_")[3]
            self.add_schedule_confirm(call, end_time)
        elif data == "master_schedule":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.show_master_schedule(message)
        elif data == "master_clients":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.show_master_appointments(message)
        elif data == "add_schedule":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.add_schedule_start(message)
        elif data == "add_service":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.add_service_start(message)
        elif data == "delete_schedule":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.delete_schedule_start(message)
        elif data == "client_mode":
            # Конвертируем call в message-объект для совместимости
            message = types.Message()
            message.chat = call.message.chat
            message.from_user = call.from_user
            self.client_mode(message)
    
    def show_master_info(self, call, master_id):
        """Показать информацию о мастере и его услуги"""
        masters = self.db.get_masters()
        master = next((m for m in masters if m[0] == master_id), None)
        
        if not master:
            self.bot.edit_message_text(
                "Мастер не найден.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        services = self.db.get_services_by_master(master_id)
        
        if not services:
            self.bot.edit_message_text(
                "У этого мастера пока нет услуг.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        text = MESSAGES['master_info'].format(
            address=master[5],
            social_media=master[4]
        )
        
        markup = types.InlineKeyboardMarkup()
        for service in services:
            duration_str = TimeUtils.format_duration(service[4])
            button_text = f"{service[2]} - {service[3]} руб. ({duration_str})"
            button = types.InlineKeyboardButton(button_text, callback_data=f"service_{service[0]}")
            markup.add(button)
        
        if call.from_user.id not in self.user_data:
            self.user_data[call.from_user.id] = {}
        self.user_data[call.from_user.id]['selected_master'] = master_id
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def show_available_dates(self, call):
        """Показать доступные даты на основе реального расписания мастера"""
        user_data = self.user_data.get(call.from_user.id, {})
        master_id = user_data.get('selected_master')
        
        if not master_id:
            self.bot.edit_message_text(
                "Ошибка: не выбран мастер.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Получаем реальные даты из расписания мастера
        master_schedule = self.db.get_master_schedule(master_id)
        
        if not master_schedule:
            self.bot.edit_message_text(
                "У выбранного мастера пока нет доступного расписания.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Создаем список уникальных дат из расписания
        available_dates = []
        for schedule_entry in master_schedule:
            date_str = schedule_entry[2]  # date
            if date_str not in [d[0] for d in available_dates]:
                formatted_date = TimeUtils.format_date_russian(date_str)
                available_dates.append((date_str, formatted_date))
        
        if not available_dates:
            self.bot.edit_message_text(
                "У выбранного мастера пока нет доступного расписания.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for date_str, formatted_date in available_dates:
            button = types.InlineKeyboardButton(formatted_date, callback_data=f"date_{date_str}")
            markup.add(button)
        
        self.bot.edit_message_text(
            "Выберите дату:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def show_available_times(self, call):
        """Показать доступное время"""
        user_data = self.user_data.get(call.from_user.id, {})
        master_id = user_data.get('selected_master')
        date = user_data.get('selected_date')
        
        if not master_id or not date:
            self.bot.edit_message_text(
                "Ошибка: не выбран мастер или дата.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Получаем расписание мастера на выбранную дату
        schedule = self.db.get_available_schedule(master_id, date)
        
        if not schedule:
            self.bot.edit_message_text(
                "На выбранную дату нет доступного времени.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Получаем существующие записи на эту дату для этого мастера
        existing_appointments = self.db.get_appointments_by_date(date)
        # Фильтруем только записи к выбранному мастеру
        existing_appointments = [app for app in existing_appointments if app[2] == master_id]
        
        # Отладочная информация
        logger.info(f"Расписание мастера {master_id} на {date}: {schedule}")
        logger.info(f"Существующие записи на {date} для мастера {master_id}: {existing_appointments}")
        
        # Генерируем временные слоты
        markup = types.InlineKeyboardMarkup()
        available_slots = []
        
        for sched in schedule:
            start_time = sched[3]  # start_time
            end_time = sched[4]    # end_time
            
            time_slots = TimeUtils.generate_time_slots(start_time, end_time, 60)
            
            for time_slot in time_slots:
                # Проверяем, не в прошлом ли время
                if not TimeUtils.is_time_in_past(date, time_slot):
                    # Получаем продолжительность выбранной услуги
                    service_duration = 60  # По умолчанию
                    if user_data.get('selected_service'):
                        services = self.db.get_services_by_master(master_id)
                        service = next((s for s in services if s[0] == user_data['selected_service']), None)
                        if service:
                            service_duration = service[4]  # duration
                    
                    # Проверяем доступность слота
                    is_available = TimeUtils.is_slot_available(time_slot, existing_appointments, service_duration)
                    logger.info(f"Слот {time_slot} доступен: {is_available}")
                    
                    if is_available:
                        button = types.InlineKeyboardButton(time_slot, callback_data=f"time_{time_slot}")
                        markup.add(button)
                        available_slots.append(time_slot)
        
        logger.info(f"Доступные слоты: {available_slots}")
        
        if markup.keyboard == []:
            self.bot.edit_message_text(
                "На выбранную дату нет доступного времени.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        self.bot.edit_message_text(
            "Выберите время:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def create_appointment(self, call, time):
        """Создать запись"""
        user_id = call.from_user.id
        user_data = self.user_data.get(user_id, {})
        
        master_id = user_data.get('selected_master')
        service_id = user_data.get('selected_service')
        date = user_data.get('selected_date')
        
        if not all([master_id, service_id, date]):
            self.bot.edit_message_text(
                "Ошибка: не все данные выбраны.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        # Создаем запись (конфликт времени уже проверен в show_available_times)
        appointment_id = self.db.create_appointment(user_id, master_id, service_id, date, time)
        
        # Получаем информацию для подтверждения
        masters = self.db.get_masters()
        master = next((m for m in masters if m[0] == master_id), None)
        services = self.db.get_services_by_master(master_id)
        service = next((s for s in services if s[0] == service_id), None)
        
        formatted_date = TimeUtils.format_date_russian(date)
        duration_str = TimeUtils.format_duration(service[4])  # service duration
        
        text = MESSAGES['appointment_created'].format(
            date=formatted_date,
            time=time,
            master=master[2],
            service=service[2],
            price=service[3]
        )
        text += f"\n⏱️ Продолжительность: {duration_str}"
        text += f"\n🔔 Мы отправим вам напоминание за час до записи!"
        
        self.bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id
        )
        
        # Очищаем пользовательские данные
        if user_id in self.user_data:
            del self.user_data[user_id]
    
    def cancel_appointment(self, call, appointment_id):
        """Отменить запись"""
        try:
            self.db.cancel_appointment(appointment_id)
            self.bot.edit_message_text(
                MESSAGES['appointment_cancelled'],
                call.message.chat.id,
                call.message.message_id
            )
        except Exception as e:
            # Если не удается отредактировать сообщение, отправляем новое
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            self.bot.send_message(
                call.message.chat.id,
                MESSAGES['appointment_cancelled']
            )
    
    def show_masters_for_login(self, call):
        """Показать список мастеров для входа"""
        masters = self.db.get_masters_list()
        
        if not masters:
            self.bot.edit_message_text(
                "Нет доступных мастеров для входа.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        markup = types.InlineKeyboardMarkup()
        for master in masters:
            button_text = f"{master[1]} ({master[2]})"  # name (specialization)
            button = types.InlineKeyboardButton(button_text, callback_data=f"login_master_{master[0]}")
            markup.add(button)
        
        self.bot.edit_message_text(
            "Выберите мастера для входа:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
    
    def start_master_registration(self, call):
        """Начать регистрацию нового мастера"""
        self.bot.edit_message_text(
            "Для работы в режиме мастера нужно зарегистрироваться.\n"
            "Отправьте данные в формате:\n"
            "МАСТЕР: Имя | Специализация | Соцсети | Адрес | Пароль\n\n"
            "Например:\n"
            "МАСТЕР: Анна Иванова | Парикмахер | @anna_hair | ул. Пушкина, 10 | mypassword123",
            call.message.chat.id,
            call.message.message_id
        )
    
    def request_master_login_password(self, call, master_id):
        """Запрос пароля для входа под конкретным мастером"""
        user_id = call.from_user.id
        
        # Сохраняем выбранного мастера
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['selected_master_for_login'] = master_id
        self.user_data[user_id]['waiting_for_master_password'] = True
        
        # Получаем имя мастера
        masters = self.db.get_masters()
        master = next((m for m in masters if m[0] == master_id), None)
        master_name = master[2] if master else "Неизвестный мастер"
        
        self.bot.edit_message_text(
            f"Введите пароль для входа под мастером '{master_name}':",
            call.message.chat.id,
            call.message.message_id
        )
    
    def process_master_registration(self, message, text):
        """Обработка регистрации мастера"""
        try:
            parts = text.replace("МАСТЕР:", "").strip().split("|")
            if len(parts) != 5:
                raise ValueError("Неверный формат")
            
            name, specialization, social_media, address, password = [p.strip() for p in parts]
            user_id = message.from_user.id
            
            master_id = self.db.add_master(user_id, name, specialization, social_media, address, password)
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for row in KEYBOARDS['master_menu']:
                markup.row(*row)
            
            self.bot.send_message(
                message.chat.id,
                f"✅ Вы успешно зарегистрированы как мастер '{name}'!\n"
                f"Пароль: {password}",
                reply_markup=markup
            )
            
        except Exception as e:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка регистрации. Проверьте формат данных.\n"
                "Формат: МАСТЕР: Имя | Специализация | Соцсети | Адрес"
            )
    
    def process_schedule_addition(self, message, text):
        """Обработка добавления расписания"""
        try:
            parts = text.replace("РАСПИСАНИЕ:", "").strip().split("|")
            if len(parts) != 3:
                raise ValueError("Неверный формат")
            
            date, start_time, end_time = [p.strip() for p in parts]
            
            # Валидация формата
            if not TimeUtils.validate_date_format(date):
                raise ValueError("Неверный формат даты")
            
            if not TimeUtils.validate_time_format(start_time) or not TimeUtils.validate_time_format(end_time):
                raise ValueError("Неверный формат времени")
            
            user_id = message.from_user.id
            
            # Проверяем, что пользователь вошел под мастером
            if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
                self.bot.send_message(message.chat.id, "Вы не вошли под мастером.")
                return
            
            master_id = self.user_data[user_id]['current_master_id']
            self.db.add_schedule(master_id, date, start_time, end_time)
            
            formatted_date = TimeUtils.format_date_russian(date)
            self.bot.send_message(
                message.chat.id,
                f"✅ Расписание добавлено!\n📅 {formatted_date}\n⏰ {start_time} - {end_time}"
            )
            
        except Exception as e:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка добавления расписания. Проверьте формат.\n"
                "Формат: РАСПИСАНИЕ: ГГГГ-ММ-ДД | ЧЧ:ММ | ЧЧ:ММ\n"
                "Пример: РАСПИСАНИЕ: 2024-01-15 | 09:00 | 18:00"
            )
    
    def process_service_addition(self, message, text):
        """Обработка добавления услуги"""
        try:
            parts = text.replace("УСЛУГА:", "").strip().split("|")
            if len(parts) != 3:
                raise ValueError("Неверный формат")
            
            name, price, duration = [p.strip() for p in parts]
            price = float(price)
            duration = int(duration)
            
            if price <= 0 or duration <= 0:
                raise ValueError("Цена и продолжительность должны быть положительными")
            
            user_id = message.from_user.id
            
            # Проверяем, что пользователь вошел под мастером
            if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
                self.bot.send_message(message.chat.id, "Вы не вошли под мастером.")
                return
            
            master_id = self.user_data[user_id]['current_master_id']
            self.db.add_service(master_id, name, price, duration)
            
            duration_str = TimeUtils.format_duration(duration)
            self.bot.send_message(
                message.chat.id,
                f"✅ Услуга добавлена!\n💇‍♀️ {name}\n💰 {price} руб.\n⏱️ {duration_str}"
            )
            
        except Exception as e:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка добавления услуги. Проверьте формат.\n"
                "Формат: УСЛУГА: Название | Цена | Продолжительность(мин)\n"
                "Пример: УСЛУГА: Стрижка мужская | 1500 | 60"
            )
    
    def show_master_schedule(self, message):
        """Показать расписание мастера"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "Вы не вошли под мастером.")
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        master_name = self.user_data[user_id]['current_master_name']
        
        # Получаем расписание мастера
        schedule = self.db.get_master_schedule(master_id)
        
        if not schedule:
            self.bot.send_message(message.chat.id, f"У мастера '{master_name}' пока нет расписания.")
            return
        
        text = f"📋 Расписание мастера '{master_name}':\n\n"
        
        # Группируем по датам
        for s in schedule:
            date = s[2]  # date
            start_time = s[3]  # start_time
            end_time = s[4]  # end_time
            formatted_date = TimeUtils.format_date_russian(date)
            text += f"📅 {formatted_date}:\n"
            text += f"   ⏰ {start_time} - {end_time}\n\n"
        
        self.bot.send_message(message.chat.id, text)
    
    def delete_schedule_start(self, message):
        """Начало удаления расписания"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "Вы не вошли под мастером.")
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        master_name = self.user_data[user_id]['current_master_name']
        
        # Получаем расписание мастера
        schedule = self.db.get_master_schedule(master_id)
        
        if not schedule:
            self.bot.send_message(message.chat.id, f"У мастера '{master_name}' пока нет расписания.")
            return
        
        # Создаем клавиатуру для выбора даты
        markup = types.InlineKeyboardMarkup()
        
        for s in schedule:
            date = s[2]  # date
            schedule_id = s[0]  # id
            formatted_date = TimeUtils.format_date_russian(date)
            button_text = f"🗑️ {formatted_date}"
            button = types.InlineKeyboardButton(button_text, callback_data=f"delete_schedule_{schedule_id}")
            markup.add(button)
        
        markup.add(types.InlineKeyboardButton("🗑️ Удалить всё расписание", callback_data="delete_all_schedule"))
        
        self.bot.send_message(
            message.chat.id,
            f"🗑️ Удаление расписания мастера '{master_name}'\n\nВыберите что удалить:",
            reply_markup=markup
        )
    
    def delete_specific_schedule(self, call, schedule_id):
        """Удалить конкретное расписание"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        master_name = self.user_data[user_id]['current_master_name']
        
        # Удаляем конкретное расписание
        self.db.delete_schedule_by_id(schedule_id)
        
        self.bot.edit_message_text(
            f"✅ Расписание для мастера '{master_name}' удалено!",
            call.message.chat.id,
            call.message.message_id
        )
    
    def delete_all_schedule(self, call):
        """Удалить всё расписание мастера"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        master_name = self.user_data[user_id]['current_master_name']
        
        # Удаляем всё расписание мастера
        self.db.delete_master_schedule(master_id)
        
        self.bot.edit_message_text(
            f"✅ Всё расписание мастера '{master_name}' удалено!",
            call.message.chat.id,
            call.message.message_id
        )
    
    def delete_service_start(self, message):
        """Начало удаления услуги"""
        user_id = message.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.send_message(message.chat.id, "❌ Вы не вошли под мастером.")
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        master_name = self.user_data[user_id]['current_master_name']
        
        # Получаем услуги мастера
        services = self.db.get_services_by_master(master_id)
        
        if not services:
            self.bot.send_message(message.chat.id, f"У мастера '{master_name}' пока нет услуг.")
            return
        
        # Создаем клавиатуру для выбора услуги
        markup = types.InlineKeyboardMarkup()
        
        for service in services:
            service_id = service[0]  # id
            service_name = service[2]  # name
            service_price = service[3]  # price
            service_duration = service[4]  # duration
            
            duration_str = TimeUtils.format_duration(service_duration)
            button_text = f"🗑️ {service_name} - {service_price} руб. ({duration_str})"
            button = types.InlineKeyboardButton(button_text, callback_data=f"delete_service_{service_id}")
            markup.add(button)
        
        markup.add(types.InlineKeyboardButton("🗑️ Удалить все услуги", callback_data="delete_all_services"))
        
        self.bot.send_message(
            message.chat.id,
            f"🗑️ Удаление услуг мастера '{master_name}'\n\nВыберите услугу для удаления:",
            reply_markup=markup
        )
    
    def delete_specific_service(self, call, service_id):
        """Удалить конкретную услугу"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "❌ Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        master_name = self.user_data[user_id]['current_master_name']
        
        # Удаляем конкретную услугу
        self.db.delete_service_by_id(service_id)
        
        self.bot.edit_message_text(
            f"✅ Услуга мастера '{master_name}' удалена!",
            call.message.chat.id,
            call.message.message_id
        )
    
    def delete_all_services(self, call):
        """Удалить все услуги мастера"""
        user_id = call.from_user.id
        
        # Проверяем, что пользователь вошел под мастером
        if user_id not in self.user_data or not self.user_data[user_id].get('current_master_id'):
            self.bot.edit_message_text(
                "❌ Вы не вошли под мастером.",
                call.message.chat.id,
                call.message.message_id
            )
            return
        
        master_id = self.user_data[user_id]['current_master_id']
        master_name = self.user_data[user_id]['current_master_name']
        
        # Удаляем все услуги мастера
        self.db.delete_master_services(master_id)
        
        self.bot.edit_message_text(
            f"✅ Все услуги мастера '{master_name}' удалены!",
            call.message.chat.id,
            call.message.message_id
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Salon Bot запущен!")
        
        while True:
            try:
                self.bot.polling(none_stop=True, interval=1, timeout=20)
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Ошибка в боте: {e}")
                logger.info("🔄 Перезапуск бота через 5 секунд...")
                import time
                time.sleep(5)