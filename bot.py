"""
Telegram-бот для управления событиями и встречами.
Интеграция с Django для работы с БД.
"""
import os
import sys
import psycopg2
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters
)

# --- Загрузка секретов из переменных окружения ---
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN! Проверьте файл .env")

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    missing = [k for k, v in
               {'DB_HOST': DB_HOST, 'DB_NAME': DB_NAME, 'DB_USER': DB_USER, 'DB_PASSWORD': DB_PASSWORD}.items() if
               not v]
    raise RuntimeError(f"Не заданы переменные окружения для БД: {', '.join(missing)}. Проверьте .env")

# --- Настройка Django ---
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, 'admin_panel'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.settings")
import django
django.setup()

# --- Импорт обработчиков и календаря ---
from bot_calendar import Calendar
from bot_handlers import (
    start_handler, register_handler, login_handler, calendar_handler,
    my_stats_handler, event_create_handler, event_read_handler,
    event_edit_handler, event_delete_handler, event_show_all_handler,
    public_events_handler, share_event_handler, export_events_handler,
    public_callback_handler, menu_callback_handler, invite_meeting, my_meetings,
    meeting_message_handler, meeting_callback_handler, text_handler,
)

# --- Подключение к БД ---
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
except Exception as e:
    print(f"Ошибка подключения к БД: {e}")
    sys.exit(1)

calendar = Calendar(conn, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)

# Передаём calendar в bot_handlers
import bot_handlers
bot_handlers.calendar = calendar

# --- Сброс последовательности ID при пустом календаре ---
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM events;")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("ALTER SEQUENCE events_id_seq RESTART WITH 1;")
            conn.commit()
            print("Последовательность ID сброшена (календарь пуст)")
except Exception as e:
    print(f"Не удалось сбросить последовательность: {e}")


def make_calendar_handler(handler):
    """Обёртка для передачи calendar в обработчики."""
    def wrapper(update, context):
        return handler(update, context)
    return wrapper


def main():
    """Настройка и запуск бота."""
    updater = Updater(API_TOKEN)
    dispatcher = updater.dispatcher

    # Основные команды
    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('register', register_handler))
    dispatcher.add_handler(CommandHandler('login', login_handler))

    # Команды календаря
    dispatcher.add_handler(CommandHandler('calendar', make_calendar_handler(calendar_handler)))
    dispatcher.add_handler(CommandHandler('my_stats', my_stats_handler))
    dispatcher.add_handler(CommandHandler('create_event', make_calendar_handler(event_create_handler)))
    dispatcher.add_handler(CommandHandler('read_event', make_calendar_handler(event_read_handler)))
    dispatcher.add_handler(CommandHandler('edit_event', make_calendar_handler(event_edit_handler)))
    dispatcher.add_handler(CommandHandler('delete_event', make_calendar_handler(event_delete_handler)))
    dispatcher.add_handler(CommandHandler('all_events', make_calendar_handler(event_show_all_handler)))
    dispatcher.add_handler(CommandHandler('public_events', make_calendar_handler(public_events_handler)))
    dispatcher.add_handler(CommandHandler('share_event', make_calendar_handler(share_event_handler)))

    # Callback-обработчики
    dispatcher.add_handler(CallbackQueryHandler(
        make_calendar_handler(public_callback_handler), pattern=r"^public_"
    ))
    dispatcher.add_handler(CallbackQueryHandler(menu_callback_handler, pattern=r"^menu_"))

    # Команды встреч
    dispatcher.add_handler(CommandHandler('invite_meeting', invite_meeting))
    dispatcher.add_handler(CommandHandler('my_meetings', my_meetings))
    dispatcher.add_handler(CallbackQueryHandler(meeting_callback_handler, pattern=r"^(confirm|decline)_"))

    # Экспорт и текстовые сообщения
    dispatcher.add_handler(CommandHandler('export', export_events_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    print("Бот запущен и ждёт команд...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
