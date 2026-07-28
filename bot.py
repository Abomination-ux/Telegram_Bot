import os
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Токен не задан! Установите переменную TELEGRAM_BOT_TOKEN")

START_DATE = datetime(2026, 7, 27)
CHANNEL_ID = -1003881790405  # Убедитесь, что это верный ID канала!

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
    
    # 1. Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # 2. Хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # 3. Запускаем планировщик (он работает в фоне, используя тот же цикл событий)
    scheduler = AsyncIOScheduler()
    # Если вы в Москве, поставьте hour=10, UTC+3 даст 13:00. 
    # Сейчас стоит 10:00 по UTC.
    scheduler.add_job(daily_notification, CronTrigger(hour=10, minute=0))
    scheduler.start()
    logging.info("✅ Планировщик запущен.")

    # 4. Настройки для Webhook
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')
    
    if not webhook_url:
        logging.error("❌ ОШИБКА: Переменная WEBHOOK_URL не найдена!")
        return

    logging.info(f"🚀 Запуск Webhook на порту {port}...")

    # 5. Запускаем бота. 
    # ВАЖНО: В версии 20.x python-telegram-bot мы используем await, и запускаем через asyncio.run()
    await application.initialize()
    await application.start()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{webhook_url}/{TOKEN}"
    )
    
    logging.info("✅ Бот начал слушать сообщения.")
    
    # Бесконечное ожидание, чтобы бот не выключился
    stop_signal = asyncio.Future()
    await stop_signal

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен.")
