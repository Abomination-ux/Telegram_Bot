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

# Отдельная асинхронная функция для настройки планировщика
async def setup_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily_notification, CronTrigger(hour=10, minute=0))
    scheduler.start()
    logging.info("✅ Планировщик успешно запущен в фоне!")

def main():
    global application
    
    # 1. Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # 2. Добавляем хендлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # 3. Запускаем Webhook
    port = int(os.environ.get('PORT', 8443))
    webhook_url = os.environ.get('WEBHOOK_URL')

    if not webhook_url:
        logging.error("❌ ОШИБКА: Переменная WEBHOOK_URL не найдена!")
        return

    logging.info(f"🚀 Запуск Webhook на порту {port}...")

    # Сначала запускаем вебхук
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{webhook_url}/{TOKEN}"
        # post_init мы убрали
    )

    # !!! ВАЖНО: Код после run_webhook выполнится ТОЛЬКО когда бот будет остановлен.
    # Поэтому нам нужно запустить планировщик ДО того, как мы вызовем run_webhook,
    # но ПРЯМО ВНУТРИ этого же процесса, чтобы он работал в фоне.
    
    # Создаем свой собственный небольшой цикл событий для планировщика
    # (так как run_webhook блокирует поток выполнения)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Запускаем настройку планировщика в этом цикле (это устранит ошибку no running event loop)
    loop.run_until_complete(setup_scheduler())
    
    # Теперь запускаем самого бота. Он заберет управление циклом на себя.
    # Планировщик при этом продолжит тихо работать в фоне.
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"{webhook_url}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
