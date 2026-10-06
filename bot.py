# Стандартная библиотека
import os
import sys

# Сторонние пакеты
import psycopg2
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
)

# Токен бота из переменных окружения
API_TOKEN = os.getenv("API_TOKEN", "8603042436:AAHZIrnlqmdYgzKC-tsVzAKJ0gEBaQDjS0o")

# Корректно определяем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin_panel'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.settings")

import django
django.setup()

from bot_calendar import Calendar
from bot_handlers import (
    start_handler, register_handler, login_handler, calendar_handler,
    my_stats_handler, event_create_handler, event_read_handler,
    event_edit_handler, event_delete_handler, event_show_all_handler,
    public_events_handler, share_event_handler, export_events_handler,
    public_callback_handler, invite_meeting, my_meetings,
    meeting_message_handler, meeting_callback_handler, text_handler,
)

# Подключение к БД
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'telegram_bot_db'),
        user=os.getenv('DB_USER', 'bot_user'),
        password=os.getenv('DB_PASSWORD', 'Gfhflbc1996')
    )
except Exception as e:
    print(f"Ошибка подключения к БД: {e}")
    sys.exit(1)

calendar = Calendar(conn)


def make_calendar_handler(handler):
    """Обёртка для передачи calendar в обработчики."""
    def wrapper(update, context):
        return handler(update, context, calendar)
    return wrapper


def main():
    updater = Updater(token=API_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Пользователи
    dp.add_handler(CommandHandler('start', start_handler))
    dp.add_handler(CommandHandler('register', register_handler))
    dp.add_handler(CommandHandler('login', login_handler))

    # Календарь и события
    dp.add_handler(CommandHandler('calendar', make_calendar_handler(calendar_handler)))
    dp.add_handler(CommandHandler('my_stats', my_stats_handler))
    dp.add_handler(CommandHandler('create_event', make_calendar_handler(event_create_handler)))
    dp.add_handler(CommandHandler('read_event', make_calendar_handler(event_read_handler)))
    dp.add_handler(CommandHandler('edit_event', make_calendar_handler(event_edit_handler)))
    dp.add_handler(CommandHandler('delete_event', make_calendar_handler(event_delete_handler)))
    dp.add_handler(CommandHandler('all_events', make_calendar_handler(event_show_all_handler)))
    dp.add_handler(CommandHandler('public_events', make_calendar_handler(public_events_handler)))
    dp.add_handler(CommandHandler('share_event', make_calendar_handler(share_event_handler)))
    dp.add_handler(CallbackQueryHandler(
        make_calendar_handler(public_callback_handler), pattern=r"^public_"
    ))

    # Встречи
    dp.add_handler(CommandHandler('invite_meeting', invite_meeting))
    dp.add_handler(CommandHandler('my_meetings', my_meetings))
    dp.add_handler(CallbackQueryHandler(meeting_callback_handler, pattern=r"^(confirm|decline)_"))

    # Экспорт
    dp.add_handler(CommandHandler('export', export_events_handler))

    # Текстовые сообщения (для многошагового ввода встреч)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    print("Бот запущен и ждёт команд...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
