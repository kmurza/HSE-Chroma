#!/usr/bin/env python3
"""
Главный файл для запуска Telegram бота салона красоты

Для запуска выполните:
python main.py
"""

import sys
import os
import logging

# Добавляем путь к модулям проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.bot import SalonBot
    from config.settings import BOT_TOKEN
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что все модули установлены: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Главная функция запуска бота"""
    
    # Проверяем токен
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: Не настроен токен бота!")
        print("Откройте файл config/settings.py и замените BOT_TOKEN на ваш токен")
        print("Получить токен можно у @BotFather в Telegram")
        return
    
    # Создаем необходимые папки
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Настройка логирования
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Запуск Salon Bot...")
        
        # Создаем и запускаем бота
        bot = SalonBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте логи в папке logs/ для подробностей")

if __name__ == "__main__":
    print("🤖 Salon Booking Bot")
    print("=" * 30)
    main()
