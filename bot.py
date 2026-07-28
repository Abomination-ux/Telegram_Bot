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
CHANNEL_ID = -1003881790405

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

async def setup_scheduler():
    scheduler = AsyncIOScheduler()
    # ЗДЕСЬ ИСПРАВЛЕНО ВРЕМЯ (13:00 вместо 10:00)
    scheduler.add_job(daily_notification, CronTrigger(hour=13, minute=0)) 
    scheduler.start()
    logging.info("✅ Планировщик успешно запущен в фоне!")

def main():
    global application
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')

    if not webhook_url:
        logging.error("❌ ОШИБКА: Переменная WEBHOOK_URL не найдена!")
        return

    logging.info(f"🚀 Запуск Webhook на порту {port}...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_scheduler())
    
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="secret_path_for_webhook", # ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ
        webhook_url=f"{webhook_url}/secret_path_for_webhook" # ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ
    )

if __name__ == "__main__":
    main()
