<h1 align="center">🔥 TaxiBot 🔥</h1>
<h3 align="center">Telegram Bot</h3>

---
## Описание

### Возможности бота:

🌵 Регистрация клиентов/таксистов

🌵 Создание/принятие заказов

🌵 Админ-панель

🌵 История заказов

🌵 Отправка геопозиции, определение адреса и расстояния и стоимости по координатам

🌵 Активация/деактивация водителей, рассылка (для админа)




---

## Инструкция по развертыванию

1. `cd TaxiBotVSG`
2. `python3.10 -m venv venv` - создание виртуального окружения.
3. `source venv/bin/activate` - активация виртуального окружения.
4. `pip install -r requirements.txt` - подключить все библиотеки проекта.
5. `touch /etc/systemd/system/bot.service`
6. `touch /root/TaxiBotVSG/database/Taxi.db`
7. прописать в файле п.5 код:
[Unit]
Description=TaxiBot
After=network.target

[Service]
WorkingDirectory=/root/TaxiBotVSG
ExecStart=/root/TaxiBotVSG/venv/bin/python/root/TaxiBotVSG/main.py
Restart=always

[Install]
WantedBy=multi-user.target

---

## Инструкция по запуску

1. Создайте бота в Telegram через BotFather и получите токен для использования API.
2. `touch .env` - создайть файл .env  подробнее написано в `.env.template`
3. `echo "BOT_TOKEN=your_bot_token" >> .env` - добавить Токен бота
4. `echo "ADMIN_ID=your_admin_id" >> .env` - добавить Телеграм id админа
3. Запустите файл `main.py`
