import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Токен берется из переменной окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Токен не задан! Установите переменную TELEGRAM_BOT_TOKEN")

START_DATE = datetime(2026, 7, 27)
CHANNEL_ID = -1003881790405   # ЗАМЕНИТЕ на реальный ID канала

logging.basicConfig(level=logging.INFO)
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Бот настроен на канал. Каждый день в 10:00 туда будет приходить отчёт.\n"
        f"Дата отсчёта: {START_DATE.strftime('%d.%m.%Y')}"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delta = datetime.now() - START_DATE
    days = delta.days
    await update.message.reply_text(f"📅 Прошло {days} дней.")

async def daily_notification():
    delta = datetime.now() - START_DATE
    days = delta.days
    text = f"🔔 Прошёл {days} день с {START_DATE.strftime('%d.%m.%Y')}."
    try:
        await application.bot.send_message(chat_id=CHANNEL_ID, text=text)
    except Exception as e:
        logging.error(f"Ошибка отправки в канал: {e}")

async def main():
    global application
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_notification, CronTrigger(hour=10, minute=0))
    scheduler.start()

    # === ИЗМЕНЕНИЯ ДЛЯ RAILWAY ===
    
    # 1. Получаем порт, который Railway назначит автоматически (по умолчанию 8443, если не задан)
    port = int(os.environ.get('PORT', 8443))
    
    # 2. Получаем внешний URL вашего сервиса (надо будет добавить его в переменные на Railway!)
    webhook_url = os.environ.get('WEBHOOK_URL')
    if not webhook_url:
        logging.error("КРИТИЧЕСКАЯ ОШИБКА: Не задана переменная окружения WEBHOOK_URL!")
        logging.error("Бот не сможет запуститься. Добавьте её в Railway.")
        return

    # 3. Запускаем Webhook вместо Polling
    # listen="0.0.0.0" — обязательно для облачных серверов, чтобы принимать запросы извне
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,  # Используем токен как часть пути для безопасности
        webhook_url=f"{webhook_url}/{TOKEN}" # Сообщаем Telegram точный адрес
    )
    
    # === КОНЕЦ ИЗМЕНЕНИЙ ===

    # Держим бота активным (бесконечный цикл) - при webhook это работает корректно без конфликтов
    print(f"✅ Бот запущен на Webhook! Порт: {port}")
    print("Нажмите Ctrl+C для остановки.")
    
    try:
        # При webhook бот сам держит соединение, while True с asyncio.sleep(1) больше не нужен.
        # Но можно оставить, если хотите, чтобы бот не завершался при ошибках webhook.
        # run_webhook уже является блокирующим вызовом (он держит программу запущенной).
        # Если мы дошли до этого места, значит run_webhook завершился (например, при Ctrl+C).
        pass 
    except KeyboardInterrupt:
        # В новых версиях python-telegram-bot при использовании run_webhook 
        # останавливать приложение вручную через try/except часто не требуется, 
        # но оставлю для страховки, если вы используете старую логику запуска.
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
