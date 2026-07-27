import os  # <-- Добавьте эту строку в самое начало
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Токен теперь берется из переменной окружения, а не прописан в коде
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Токен не задан! Установите переменную TELEGRAM_BOT_TOKEN")
START_DATE = datetime(2026, 7, 27)
CHANNEL_ID = -1001234567890   # ЗАМЕНИТЕ на реальный ID канала

logging.basicConfig(level=logging.INFO)
application = None

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

    # Ручной запуск бота без автоматического закрытия цикла
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Держим бота активным (бесконечный цикл)
    print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
