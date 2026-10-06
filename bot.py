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


# --- Заглушки функций для заметок ---

def create_note(note_text, note_name):
    print(f"[DEBUG] Создана заметка: name={note_name}, text={note_text}")

def read_note(note_name):
    return "Текст заметки (заглушка)"

def edit_note(note_name, note_text):
    print(f"[DEBUG] Заметка {note_name} изменена: {note_text}")

def delete_note(note_name):
    print(f"[DEBUG] Заметка {note_name} удалена")

def get_all_notes():
    return ["Заметка 1", "Заметка 2", "Заметка 3"]

def get_sorted_notes():
    return sorted(get_all_notes())


# --- Глобальный объект календаря ---
calendar = Calendar()


# --- Обработчики заметок ---

def create_note_handler(update, context):
    try:
        note_text = update.message.text
        note_name = update.message.chat_id
        create_note(note_text, note_name)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Заметка {note_name} создана."
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )

def read_note_handler(update, context):
    try:
        note_name = context.args[0] if context.args else str(update.message.chat_id)
        note_text = read_note(note_name)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Заметка {note_name}:\n{note_text}"
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )

def edit_note_handler(update, context):
    try:
        note_name = context.args[0] if context.args else str(update.message.chat_id)
        note_text = " ".join(context.args[1:]) if len(context.args) > 1 else ""
        edit_note(note_name, note_text)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Заметка {note_name} отредактирована."
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )

def delete_note_handler(update, context):
    try:
        note_name = context.args[0] if context.args else str(update.message.chat_id)
        delete_note(note_name)
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Заметка {note_name} удалена."
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )

def show_all_notes_handler(update, context):
    try:
        notes = get_all_notes()
        notes_text = "\n".join(notes) if notes else "Заметок нет."
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Все заметки:\n{notes_text}"
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )

def show_sorted_notes_handler(update, context):
    try:
        notes = get_sorted_notes()
        notes_text = "\n".join(notes) if notes else "Заметок нет."
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"Заметки (отсортированы):\n{notes_text}"
        )
    except Exception:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Произошла ошибка."
        )


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

    # Обработчики заметок
    dispatcher.add_handler(CommandHandler('create', create_note_handler))
    dispatcher.add_handler(CommandHandler('read', read_note_handler))
    dispatcher.add_handler(CommandHandler('edit', edit_note_handler))
    dispatcher.add_handler(CommandHandler('delete', delete_note_handler))
    dispatcher.add_handler(CommandHandler('all', show_all_notes_handler))
    dispatcher.add_handler(CommandHandler('sorted', show_sorted_notes_handler))

    # Обработчики календаря
    dispatcher.add_handler(CommandHandler('create_event', event_create_handler))
    dispatcher.add_handler(CommandHandler('read_event', event_read_handler))
    dispatcher.add_handler(CommandHandler('edit_event', event_edit_handler))
    dispatcher.add_handler(CommandHandler('delete_event', event_delete_handler))
    dispatcher.add_handler(CommandHandler('all_events', event_show_all_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
