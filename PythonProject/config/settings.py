# Конфигурация бота
import os

# Токен бота (замените на ваш токен)
BOT_TOKEN = os.getenv('BOT_TOKEN', "8240254652:AAFU97q-kawr1Dm5oAjsKYBipSzXqnMl268")

# Пути к файлам
DATABASE_PATH = "data/salon_bot.db"

# Настройки напоминаний
REMINDER_HOUR = 10  # Час отправки напоминаний (10:00)

# ID администратора (замените на ваш Telegram ID)
ADMIN_ID = int(os.getenv('ADMIN_ID', 123456789))

# Пароль для входа в режим мастера
MASTER_PASSWORD = os.getenv('MASTER_PASSWORD', 'master123')

# Сообщения
MESSAGES = {
    'welcome': "Добро пожаловать в бот записи к мастерам! 👋\n\nВыберите действие:",
    'choose_service': "Выберите тип услуги:",
    'choose_master': "Выберите мастера:",
    'master_info': "📍 Адрес: {address}\n🔗 Соцсети: {social_media}\n\nВыберите услугу:",
    'choose_date': "Выберите дату:",
    'choose_time': "Выберите время:",
    'appointment_created': "✅ Запись создана!\n\n📅 Дата: {date}\n⏰ Время: {time}\n👨‍💼 Мастер: {master}\n💇‍♀️ Услуга: {service}\n💰 Цена: {price} руб.",
    'reminder': "⏰ Напоминание!\n\nУ вас завтра запись:\n📅 {date}\n⏰ {time}\n👨‍💼 Мастер: {master}\n💇‍♀️ Услуга: {service}",
    'no_appointments': "У вас нет активных записей",
    'appointment_cancelled': "❌ Запись отменена",
    'master_menu': "Меню мастера:\n\nВыберите действие:",
    'schedule_added': "✅ Расписание добавлено",
    'service_added': "✅ Услуга добавлена",
    'master_password_prompt': "🔐 Введите пароль для входа в режим мастера:",
    'master_password_wrong': "❌ Неверный пароль! Попробуйте еще раз или вернитесь в главное меню.",
    'master_password_correct': "✅ Пароль верный! Добро пожаловать в режим мастера."
}

# Кнопки клавиатуры
KEYBOARDS = {
    'main_menu': [
        ['📅 Записаться', '📋 Мои записи'],
        ['❌ Отменить запись', '👨‍💼 Режим мастера']
    ],
    'master_menu': [
        ['📅 Добавить расписание', '👥 Мои клиенты'],
        ['📋 Просмотр расписания', '🗑️ Удалить расписание'],
        ['💇‍♀️ Добавить услугу', '🗑️ Удалить услугу'],
        ['👤 Режим клиента']
    ],
    'cancel_menu': [
        ['🔙 Назад в меню']
    ]
}
