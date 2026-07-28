import os
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

# Глобальная переменная для бота и планировщика
application = None
scheduler = None

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

# Эта функция запустится вместе с ботом, используя его цикл событий
async def initialize_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler()
    # Поставьте нужный час (UTC). Для Москвы (UTC+3), чтобы было 10:00, ставьте hour=7
    scheduler.add_job(daily_notification, CronTrigger(hour=10, minute=0))
    scheduler.start()
    logging.info("✅ Планировщик успешно запущен в фоне!")

def main():
    global application
    
    logging.info("🚀 Запуск бота через Polling...")

    # 1. Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # 2. Добавляем хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # 3. Запускаем планировщик используя post_init
    # Это скажет библиотеке: "Как только запустишь свой цикл, вызови initialize_scheduler"
    application.run_polling(
        post_init=initialize_scheduler
    )

if __name__ == "__main__":
    main()
