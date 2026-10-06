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

    def create_event(self, event_name, event_date, event_time, event_details):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO events (name, date, time, details) "
            "VALUES (%s, %s, %s, %s) RETURNING id;",
            (event_name, event_date, event_time, event_details)
        )
        event_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return event_id

    def read_event(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, date, time, details FROM events WHERE id = %s;",
            (event_id,)
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

    def edit_event(self, event_id, event_name=None, event_date=None,
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

        values.append(event_id)
        cursor.execute(
            f"UPDATE events SET {', '.join(updates)} WHERE id = %s;",
            values
        )
        self.conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success

    def delete_event(self, event_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = %s;", (event_id,))
        self.conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success

    def get_all_events(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, date, time FROM events ORDER BY id;"
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {"id": row[0], "name": row[1], "date": row[2], "time": row[3]}
            for row in rows
        ]



# Глобальный объект календаря
calendar = Calendar(conn)



# --- Обработчики календаря ---

def event_create_handler(update, context):
    try:
        event_name = update.message.text[14:]
        event_date = "2026-10-06"
        event_time = "14:00"
        event_details = "Описание события"

        event_id = calendar.create_event(event_name, event_date, event_time, event_details)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Событие {event_name} создано и имеет номер {event_id}."
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="При создании события произошла ошибка."
        )

def event_read_handler(update, context):
    try:
        event_id = int(context.args[0])
        event = calendar.read_event(event_id)
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
        context.bot.send_message(chat_id=update.message.chat_id, text=text)
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="При чтении события произошла ошибка. Используйте: /read_event <id>"
        )

def event_edit_handler(update, context):
    try:
        event_id = int(context.args[0])
        event_name = " ".join(context.args[1:]) if len(context.args) > 1 else None

        success = calendar.edit_event(event_id, event_name=event_name)
        if success:
            text = f"Событие {event_id} отредактировано."
        else:
            text = f"Событие с номером {event_id} не найдено."
        context.bot.send_message(chat_id=update.message.chat_id, text=text)
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="При редактировании произошла ошибка. Используйте: /edit_event <id> <новое название>"
        )

def event_delete_handler(update, context):
    try:
        event_id = int(context.args[0])
        success = calendar.delete_event(event_id)
        if success:
            text = f"Событие {event_id} удалено."
        else:
            text = f"Событие с номером {event_id} не найдено."
        context.bot.send_message(chat_id=update.message.chat_id, text=text)
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="При удалении произошла ошибка. Используйте: /delete_event <id>"
        )

def event_show_all_handler(update, context):
    try:
        events = calendar.get_all_events()
        if events:
            lines = []
            for e in events:
                lines.append(f"№{e['id']}: {e['name']} — {e['date']} {e['time']}")
            text = "Все события:\n" + "\n".join(lines)
        else:
            text = "Событий пока нет."
        context.bot.send_message(chat_id=update.message.chat_id, text=text)
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="При получении списка событий произошла ошибка."
        )


# --- Инициализация и регистрация ---

def main():
    updater = Updater(token=API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('create_event', event_create_handler))
    dispatcher.add_handler(CommandHandler('read_event', event_read_handler))
    dispatcher.add_handler(CommandHandler('edit_event', event_edit_handler))
    dispatcher.add_handler(CommandHandler('delete_event', event_delete_handler))
    dispatcher.add_handler(CommandHandler('all_events', event_show_all_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
