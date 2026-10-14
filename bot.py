import os
import sys
import psycopg2
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# --- Проверка переменных окружения ---
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

# --- Импорт хендлеров и календаря ---
from bot_calendar import Calendar
from bot_handlers import (
    start_handler, register_handler, login_handler, calendar_handler,
    my_stats_handler, event_create_handler, event_read_handler,
    event_edit_handler, event_delete_handler, event_show_all_handler,
    public_events_handler, share_event_handler, export_events_handler,
    public_callback_handler, invite_meeting, my_meetings,
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

calendar = Calendar(conn)


def make_calendar_handler(handler):
    """Обёртка для передачи calendar в обработчики."""

    def wrapper(update: Update, context):
        return handler(update, context, calendar)

    return wrapper


from telegram.request import HTTPXRequest

from telegram.request import HTTPXRequest

def main():
    request = HTTPXRequest(
        connect_timeout=30.0,   # 30 секунд на установку соединения
        read_timeout=60.0,       # 60 секунд на получение ответа
        write_timeout=30.0      # 30 секунд на отправку запроса
    )

    application = (
        Application.builder()
        .token(API_TOKEN)
        .request(request)
        .build()
    )

    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CommandHandler('register', register_handler))
    application.add_handler(CommandHandler('login', login_handler))

    application.add_handler(CommandHandler('calendar', make_calendar_handler(calendar_handler)))
    application.add_handler(CommandHandler('my_stats', my_stats_handler))

    application.add_handler(CommandHandler('create_event', make_calendar_handler(event_create_handler)))
    application.add_handler(CommandHandler('read_event', make_calendar_handler(event_read_handler)))
    application.add_handler(CommandHandler('edit_event', make_calendar_handler(event_edit_handler)))
    application.add_handler(CommandHandler('delete_event', make_calendar_handler(event_delete_handler)))

    application.add_handler(CommandHandler('all_events', make_calendar_handler(event_show_all_handler)))
    application.add_handler(CommandHandler('public_events', make_calendar_handler(public_events_handler)))
    application.add_handler(CommandHandler('share_event', make_calendar_handler(share_event_handler)))

    application.add_handler(CallbackQueryHandler(
        make_calendar_handler(public_callback_handler), pattern=r"^public_"
    ))

    application.add_handler(CommandHandler('invite_meeting', invite_meeting))
    application.add_handler(CommandHandler('my_meetings', my_meetings))
    application.add_handler(CallbackQueryHandler(meeting_callback_handler, pattern=r"^(confirm|decline)_"))

    application.add_handler(CommandHandler('export', export_events_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Бот запущен и ждёт команд...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)




if __name__ == '__main__':
    main()
