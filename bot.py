# Стандартная библиотека
import os
import datetime

# Сторонние пакеты
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Локальные модули
from secrets import API_TOKEN


class Calendar:
    def __init__(self):
        self.events = {}

    def create_event(self, event_name, event_date, event_time, event_details):
        event_id = len(self.events) + 1
        event = {
            "id": event_id,
            "name": event_name,
            "date": event_date,
            "time": event_time,
            "details": event_details
        }
        self.events[event_id] = event
        return event_id

    def read_event(self, event_id):
        return self.events.get(event_id, None)

    def edit_event(self, event_id, event_name=None, event_date=None,
                   event_time=None, event_details=None):
        if event_id not in self.events:
            return False
        if event_name is not None:
            self.events[event_id]["name"] = event_name
        if event_date is not None:
            self.events[event_id]["date"] = event_date
        if event_time is not None:
            self.events[event_id]["time"] = event_time
        if event_details is not None:
            self.events[event_id]["details"] = event_details
        return True

    def delete_event(self, event_id):
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False

    def get_all_events(self):
        return list(self.events.values())


# Глобальный объект календаря
calendar = Calendar()


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
