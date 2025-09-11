# Инструкции по развертыванию

## 🌐 Развертывание на сервере

### Linux/Ubuntu сервер

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3 python3-pip python3-venv git -y

# Установка дополнительных пакетов
sudo apt install sqlite3 cron supervisor -y
```

#### 2. Клонирование проекта

```bash
# Клонирование репозитория
git clone your-repository-url salon_bot
cd salon_bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Настройка

```bash
# Копирование конфигурации
cp config/settings.py config/settings_local.py

# Редактирование настроек
nano config/settings.py
```

Установите ваши настройки:
```python
BOT_TOKEN = "your_real_bot_token"
ADMIN_ID = your_telegram_id
```

#### 4. Инициализация базы данных

```bash
python scripts/init_db.py
```

#### 5. Создание systemd сервиса

Создайте файл `/etc/systemd/system/salon-bot.service`:

```ini
[Unit]
Description=Salon Booking Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/salon_bot
Environment=PATH=/home/ubuntu/salon_bot/venv/bin
ExecStart=/home/ubuntu/salon_bot/venv/bin/python main.py
Restart=always
RestartSec=10

# Переменные окружения
Environment=BOT_TOKEN=your_bot_token
Environment=ADMIN_ID=your_admin_id

[Install]
WantedBy=multi-user.target
```

#### 6. Запуск сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable salon-bot

# Запуск сервиса
sudo systemctl start salon-bot

# Проверка статуса
sudo systemctl status salon-bot

# Просмотр логов
sudo journalctl -u salon-bot -f
```

### Docker развертывание

#### 1. Создание Dockerfile

```dockerfile
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p data logs

# Инициализация базы данных
RUN python scripts/init_db.py

# Экспорт портов (если потребуется веб-интерфейс)
EXPOSE 8000

# Команда запуска
CMD ["python", "main.py"]
```

#### 2. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  salon-bot:
    build: .
    container_name: salon-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_ID=${ADMIN_ID}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - salon-network

networks:
  salon-network:
    driver: bridge
```

#### 3. Файл .env

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
```

#### 4. Запуск

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f salon-bot

# Остановка
docker-compose down
```

## 🔐 Безопасность

### 1. Настройка SSL/TLS

Если планируете веб-интерфейс:

```bash
# Установка Certbot
sudo apt install certbot

# Получение сертификата
sudo certbot certonly --standalone -d yourdomain.com
```

### 2. Firewall

```bash
# Установка UFW
sudo apt install ufw

# Настройка правил
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Включение firewall
sudo ufw enable
```

### 3. Ротация логов

Создайте `/etc/logrotate.d/salon-bot`:

```
/home/ubuntu/salon_bot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload salon-bot
    endscript
}
```

## 📊 Мониторинг

### 1. Проверка статуса

```bash
# Статус сервиса
sudo systemctl status salon-bot

# Использование ресурсов
htop

# Размер базы данных
ls -lh data/salon_bot.db

# Статистика бота
python -c "from utils.admin_utils import AdminUtils; AdminUtils().print_statistics()"
```

### 2. Настройка алертов

Создайте скрипт проверки `/home/ubuntu/check_bot.sh`:

```bash
#!/bin/bash

# Проверка работы бота
if ! systemctl is-active --quiet salon-bot; then
    echo "Bot is down!" | mail -s "Salon Bot Alert" admin@yourdomain.com
    systemctl restart salon-bot
fi

# Проверка размера логов
LOG_SIZE=$(du -m logs/bot.log | cut -f1)
if [ $LOG_SIZE -gt 100 ]; then
    echo "Log file is too large: ${LOG_SIZE}MB" | mail -s "Salon Bot Log Alert" admin@yourdomain.com
fi
```

Добавьте в crontab:
```bash
crontab -e
# Добавьте строку:
*/5 * * * * /home/ubuntu/check_bot.sh
```

## 🔄 Обновления

### 1. Автоматическое обновление

Создайте скрипт `/home/ubuntu/update_bot.sh`:

```bash
#!/bin/bash

cd /home/ubuntu/salon_bot

# Остановка бота
sudo systemctl stop salon-bot

# Резервная копия
python -c "from utils.admin_utils import AdminUtils; AdminUtils().backup_database()"

# Обновление кода
git pull origin main

# Установка зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Запуск бота
sudo systemctl start salon-bot

echo "Bot updated successfully"
```

### 2. Миграции базы данных

При изменении структуры БД создавайте миграции:

```python
# migrations/001_add_new_field.py
from core.database import Database

def migrate():
    db = Database()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE services ADD COLUMN category TEXT')
        conn.commit()
    print("Migration 001 completed")
```

## 📱 Telegram Webhook (опционально)

Для высоконагруженных ботов:

### 1. Настройка webhook

```python
# webhook_setup.py
import requests

BOT_TOKEN = "your_bot_token"
WEBHOOK_URL = "https://yourdomain.com/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(response.json())
```

### 2. Flask приложение

```python
# webhook_app.py
from flask import Flask, request
from core.bot import SalonBot

app = Flask(__name__)
bot = SalonBot()

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    # Обработка update
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

## 🔧 Производительность

### 1. Оптимизация базы данных

```sql
-- Добавление индексов
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_client ON appointments(client_id);
CREATE INDEX idx_appointments_master ON appointments(master_id);
```

### 2. Настройка логирования

```python
# В main.py для продакшена
logging.basicConfig(
    level=logging.WARNING,  # Только предупреждения и ошибки
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        # Убираем консольный вывод
    ]
)
```

## 📋 Чеклист развертывания

- [ ] Сервер настроен и обновлен
- [ ] Python 3.8+ установлен
- [ ] Зависимости установлены
- [ ] Токен бота настроен
- [ ] База данных инициализирована
- [ ] Systemd сервис создан и запущен
- [ ] Логирование настроено
- [ ] Резервное копирование настроено
- [ ] Мониторинг настроен
- [ ] Firewall настроен
- [ ] SSL сертификат установлен (если нужен)
- [ ] Домен настроен (если нужен)
- [ ] Тестирование выполнено

## 🆘 Восстановление

### При сбое сервера:

1. Восстановите базу данных из бэкапа
2. Проверьте конфигурацию
3. Перезапустите сервис
4. Проверьте логи

### При ошибках в боте:

1. Проверьте логи: `sudo journalctl -u salon-bot -f`
2. Перезапустите сервис: `sudo systemctl restart salon-bot`
3. Проверьте статус: `sudo systemctl status salon-bot`

Готово! Ваш бот готов к продакшену! 🚀
