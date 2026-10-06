# Стандартная библиотека
import os
import datetime

# Сторонние пакеты
import telegram
import psycopg2
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Локальные модули
from secrets import API_TOKEN, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)


class Calendar:
    def __init__(self, conn):
        self.conn = conn

    def create_event(self, telegram_id, event_name, event_date, event_time, event_details):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO events (telegram_id, name, date, time, details) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (telegram_id, event_name, event_date, event_time, event_details)
        )
        event_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return event_id

    def read_event(self, telegram_id, event_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, date, time, details FROM events "
            "WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id)
        )
        row = cursor.fetchone()
        cursor.close()
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "date": row[2],
                "time": row[3],
                "details": row[4]
            }
        return None

    def edit_event(self, telegram_id, event_id, event_name=None, event_date=None,
                   event_time=None, event_details=None):
        cursor = self.conn.cursor()
        updates = []
        values = []
        if event_name is not None:
            updates.append("name = %s")
            values.append(event_name)
        if event_date is not None:
            updates.append("date = %s")
            values.append(event_date)
        if event_time is not None:
            updates.append("time = %s")
            values.append(event_time)
        if event_details is not None:
            updates.append("details = %s")
            values.append(event_details)

        if not updates:
            cursor.close()
            return False

        values.extend([event_id, telegram_id])
        cursor.execute(
            f"UPDATE events SET {', '.join(updates)} "
            f"WHERE id = %s AND telegram_id = %s;",
            values
        )
        self.conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success

    def delete_event(self, telegram_id, event_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM events WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id)
        )
        self.conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success

    def get_all_events(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, date, time FROM events "
            "WHERE telegram_id = %s ORDER BY id;",
            (telegram_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {"id": row[0], "name": row[1], "date": row[2], "time": row[3]}
            for row in rows
        ]


# Глобальный объект календаря
calendar = Calendar(conn)


# --- Вспомогательные функции ---

def is_registered(telegram_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = %s;",
        (telegram_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result is not None


def register_user(telegram_id, username):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, username) "
        "VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING;",
        (telegram_id, username)
    )
    conn.commit()
    cursor.close()


# --- Обработчики ---

def start_handler(update, context):
    user = update.effective_user
    if is_registered(user.id):
        update.message.reply_text(
            f"Привет, {user.first_name}! Вы уже зарегистрированы.\n"
            f"Доступные команды:\n"
            f"/register — повторная регистрация\n"
            f"/create_event <название> — создать событие\n"
            f"/read_event <id> — посмотреть событие\n"
            f"/edit_event <id> <новое название> — редактировать\n"
            f"/delete_event <id> — удалить событие\n"
            f"/all_events — все ваши события"
        )
    else:
        update.message.reply_text(
            f"Привет, {user.first_name}! Вы ещё не зарегистрированы.\n"
            f"Используйте /register для регистрации."
        )


def register_handler(update, context):
    user = update.effective_user
    username = user.username or user.first_name
    register_user(user.id, username)
    update.message.reply_text(
        f"Вы успешно зарегистрированы, {username}!\n"
        f"Теперь вы можете создавать события: /create_event <название>"
    )


def event_create_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    # Отслеживаем состояние пользователя
    context.user_data["state"] = "creating_event"

    try:
        event_name = update.message.text[14:]
        if not event_name.strip():
            update.message.reply_text("Укажите название события: /create_event <название>")
            context.user_data["state"] = None
            return

        event_date = "2026-10-06"
        event_time = "14:00"
        event_details = "Описание события"

        event_id = calendar.create_event(user.id, event_name, event_date, event_time, event_details)
        update.message.reply_text(
            f"Событие «{event_name}» создано и имеет номер {event_id}."
        )
        context.user_data["state"] = None
    except Exception:
        update.message.reply_text("При создании события произошла ошибка.")
        context.user_data["state"] = None


def event_read_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    context.user_data["state"] = "reading_event"

    try:
        event_id = int(context.args[0])
        event = calendar.read_event(user.id, event_id)
        if event:
            text = (
                f"Событие №{event['id']}\n"
                f"Название: {event['name']}\n"
                f"Дата: {event['date']}\n"
                f"Время: {event['time']}\n"
                f"Описание: {event['details']}"
            )
        else:
            text = f"Событие с номером {event_id} не найдено."
        update.message.reply_text(text)
    except Exception:
        update.message.reply_text(
            "При чтении события произошла ошибка. Используйте: /read_event <id>"
        )
    finally:
        context.user_data["state"] = None


def event_edit_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    context.user_data["state"] = "editing_event"

    try:
        event_id = int(context.args[0])
        event_name = " ".join(context.args[1:]) if len(context.args) > 1 else None

        success = calendar.edit_event(user.id, event_id, event_name=event_name)
        if success:
            text = f"Событие {event_id} отредактировано."
        else:
            text = f"Событие с номером {event_id} не найдено."
        update.message.reply_text(text)
    except Exception:
        update.message.reply_text(
            "При редактировании произошла ошибка. Используйте: /edit_event <id> <новое название>"
        )
    finally:
        context.user_data["state"] = None


def event_delete_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    context.user_data["state"] = "deleting_event"

    try:
        event_id = int(context.args[0])
        success = calendar.delete_event(user.id, event_id)
        if success:
            text = f"Событие {event_id} удалено."
        else:
            text = f"Событие с номером {event_id} не найдено."
        update.message.reply_text(text)
    except Exception:
        update.message.reply_text(
            "При удалении произошла ошибка. Используйте: /delete_event <id>"
        )
    finally:
        context.user_data["state"] = None


def event_show_all_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    context.user_data["state"] = "viewing_events"

    try:
        events = calendar.get_all_events(user.id)
        if events:
            lines = []
            for e in events:
                lines.append(f"№{e['id']}: {e['name']} — {e['date']} {e['time']}")
            text = "Ваши события:\n" + "\n".join(lines)
        else:
            text = "У вас пока нет событий."
        update.message.reply_text(text)
    except Exception:
        update.message.reply_text("При получении списка событий произошла ошибка.")
    finally:
        context.user_data["state"] = None


# --- Инициализация и регистрация ---

def main():
    updater = Updater(token=API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('register', register_handler))
    dispatcher.add_handler(CommandHandler('create_event', event_create_handler))
    dispatcher.add_handler(CommandHandler('read_event', event_read_handler))
    dispatcher.add_handler(CommandHandler('edit_event', event_edit_handler))
    dispatcher.add_handler(CommandHandler('delete_event', event_delete_handler))
    dispatcher.add_handler(CommandHandler('all_events', event_show_all_handler))

    print("Бот запущен и ждёт команд...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
