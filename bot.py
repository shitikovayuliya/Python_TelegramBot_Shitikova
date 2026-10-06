# Стандартная библиотека
import os
import sys
import datetime

# Сторонние пакеты
import telegram
import psycopg2
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Локальные модули
from secrets import API_TOKEN, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# --- Настройка Django ---
sys.path.append(
    "/Users/shitikova.yuliya/PycharmProjects/Python_TelegramBot_Shitikova/admin_panel"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.settings")

import django
django.setup()

from events.models import BotStatistics, Meeting, TelegramUser, Event

# --- Подключение к БД ---
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
            "SELECT id, name, date, time, details, is_public FROM events "
            "WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id)
        )
        row = cursor.fetchone()
        cursor.close()
        if row:
            return {
                "id": row[0], "name": row[1], "date": row[2],
                "time": row[3], "details": row[4], "is_public": row[5],
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
            "WHERE telegram_id = %s ORDER BY date, time;",
            (telegram_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {"id": row[0], "name": row[1], "date": row[2], "time": row[3]}
            for row in rows
        ]
    def toggle_public(self, telegram_id, event_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT is_public FROM events WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id)
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            return None
        new_status = not row[0]
        cursor.execute(
            "UPDATE events SET is_public = %s WHERE id = %s AND telegram_id = %s;",
            (new_status, event_id, telegram_id)
        )
        self.conn.commit()
        cursor.close()
        return new_status

    def get_public_events(self, telegram_id, limit=20):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, date, time, telegram_id FROM events "
            "WHERE is_public = TRUE AND telegram_id != %s "
            "ORDER BY date, time LIMIT %s;",
            (telegram_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        return [
            {"id": row[0], "name": row[1], "date": row[2],
             "time": row[3], "owner_id": row[4]}
            for row in rows
        ]



calendar = Calendar(conn)


# --- Управление пользователями через Django ORM ---

def is_registered(telegram_id):
    return TelegramUser.objects.filter(telegram_id=telegram_id).exists()


def register_user(telegram_id, username, first_name=""):
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": username or "",
            "first_name": first_name or "",
        }
    )
    if not created:
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        user.save()
    return user


def get_user(telegram_id):
    try:
        return TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return None


# --- Обработчики событий ---

def start_handler(update, context):
    user = update.effective_user
    if is_registered(user.id):
        update.message.reply_text(
            f"Привет, {user.first_name}! Вы уже зарегистрированы.\n"
            f"Доступные команды:\n"
            f"/register — повторная регистрация\n"
            f"/login — вход в личный кабинет\n"
            f"/calendar — мой календарь\n"
            f"/create_event <название> — создать событие\n"
            f"/read_event <id> — посмотреть событие\n"
            f"/edit_event <id> <новое название> — редактировать\n"
            f"/delete_event <id> — удалить событие\n"
            f"/all_events — все ваши события\n"
            f"/my_stats — моя статистика\n"
            f"/invite_meeting — пригласить на встречу\n"
            f"/my_meetings — мои встречи\n"
            f"/share_event <id> — сделать событие публичным/приватным\n"
            f"/public_events — посмотреть публичные события других пользователей\n"
            f"/export — выгрузить события в CSV или JSON\n"

        )
    else:
        update.message.reply_text(
            f"Привет, {user.first_name}! Вы ещё не зарегистрированы.\n"
            f"Используйте /register для регистрации."
        )


def register_handler(update, context):
    user = update.effective_user
    username = user.username or user.first_name or str(user.id)
    register_user(user.id, username, user.first_name or "")
    update.message.reply_text(
        f"Вы успешно зарегистрированы, {username}!\n"
        f"Теперь вам доступны:\n"
        f"/calendar — ваш календарь\n"
        f"/create_event <название> — создать событие\n"
        f"/my_stats — ваша статистика"
    )


def login_handler(update, context):
    user = update.effective_user
    tg_user = get_user(user.id)
    if tg_user:
        update.message.reply_text(
            f"Вы вошли в личный кабинет.\n"
            f"ID: {tg_user.telegram_id}\n"
            f"Имя: {tg_user.username or tg_user.first_name}\n"
            f"Событий создано: {tg_user.events_created}\n"
            f"Событий отредактировано: {tg_user.events_edited}\n"
            f"Событий удалено: {tg_user.events_cancelled}\n\n"
            f"Команды:\n"
            f"/calendar — мой календарь\n"
            f"/my_stats — моя статистика"
        )
    else:
        update.message.reply_text(
            "Вы ещё не зарегистрированы. Используйте /register."
        )


def calendar_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    # --- Мои события ---
    events = calendar.get_all_events(user.id)
    grouped = {}
    for e in events:
        date_str = str(e["date"])
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(e)

    if grouped:
        text = "📅 Ваш календарь:\n\n"
        for date_str in sorted(grouped.keys()):
            text += f"📌 {date_str}\n"
            for e in grouped[date_str]:
                text += f"   ⏰ {e['time']} — {e['name']} (№{e['id']})\n"
            text += "\n"
    else:
        text = "📅 Ваш календарь пуст. Создайте событие: /create_event <название>\n\n"

    # --- Общие события (публичные от других пользователей) ---
    public_events = calendar.get_public_events(user.id)
    if public_events:
        text += "🌍 Общие события:\n\n"
        public_grouped = {}
        for e in public_events:
            date_str = str(e["date"])
            if date_str not in public_grouped:
                public_grouped[date_str] = []
            public_grouped[date_str].append(e)

        for date_str in sorted(public_grouped.keys()):
            text += f"📌 {date_str}\n"
            for e in public_grouped[date_str]:
                # Получаем имя автора
                try:
                    owner = TelegramUser.objects.get(telegram_id=e["owner_id"])
                    owner_name = owner.username or owner.first_name or "Аноним"
                except TelegramUser.DoesNotExist:
                    owner_name = "Аноним"
                text += f"   ⏰ {e['time']} — {e['name']} (от {owner_name})\n"
            text += "\n"

    update.message.reply_text(text)


def my_stats_handler(update, context):
    user = update.effective_user
    tg_user = get_user(user.id)
    if not tg_user:
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    text = (
        f"📊 Ваша статистика:\n\n"
        f"Событий создано: {tg_user.events_created}\n"
        f"Событий отредактировано: {tg_user.events_edited}\n"
        f"Событий удалено: {tg_user.events_cancelled}\n"
    )
    update.message.reply_text(text)


def event_create_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        args = context.args
        if not args:
            update.message.reply_text("Укажите название события: /create_event <название>")
            return

        event_name = " ".join(args)
        if not event_name.strip():
            update.message.reply_text("Название не может быть пустым.")
            return

        event_date = "2026-10-06"
        event_time = "14:00"
        event_details = "Описание события"

        event_id = calendar.create_event(user.id, event_name, event_date, event_time, event_details)

        tg_user = get_user(user.id)
        if tg_user:
            tg_user.events_created += 1
            tg_user.save()

        update.message.reply_text(f"Событие «{event_name}» создано и имеет номер {event_id}.")
    except Exception as e:
        update.message.reply_text(f"При создании события произошла ошибка: {e}")


def event_read_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        if len(context.args) == 0:
            update.message.reply_text("Используйте: /read_event <id>")
            return
        event_id = int(context.args[0])
        event = calendar.read_event(user.id, event_id)
        if event:
            public_status = "да" if event.get("is_public") else "нет"
            text = (
                f"Событие №{event['id']}\n"
                f"Название: {event['name']}\n"
                f"Дата: {event['date']}\n"
                f"Время: {event['time']}\n"
                f"Описание: {event['details']}\n"
                f"Публичное: {public_status}"
            )
            button_text = (
                "Сделать приватным" if event.get("is_public") else "Сделать публичным"
            )
            keyboard = [[InlineKeyboardButton(
                button_text, callback_data=f"public_{event_id}"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text, reply_markup=reply_markup)
        else:
            update.message.reply_text(f"Событие с номером {event_id} не найдено.")
    except ValueError:
        update.message.reply_text("ID события должно быть числом. Используйте: /read_event <id>")
    except Exception as e:
        update.message.reply_text(f"При чтении события произошла ошибка: {e}")



def event_edit_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        if len(context.args) < 1:
            update.message.reply_text("Используйте: /edit_event <id> <новое название>")
            return

        event_id = int(context.args[0])
        event_name = " ".join(context.args[1:]) if len(context.args) > 1 else None

        success = calendar.edit_event(user.id, event_id, event_name=event_name)
        if success:
            tg_user = get_user(user.id)
            if tg_user:
                tg_user.events_edited += 1
                tg_user.save()
            text = f"Событие {event_id} отредактировано."
        else:
            text = f"Событие с номером {event_id} не найдено или не принадлежит вам."
        update.message.reply_text(text)
    except ValueError:
        update.message.reply_text("ID события должно быть числом.")
    except Exception as e:
        update.message.reply_text(f"При редактировании произошла ошибка: {e}")


def event_delete_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        if len(context.args) == 0:
            update.message.reply_text("Используйте: /delete_event <id>")
            return
        event_id = int(context.args[0])
        success = calendar.delete_event(user.id, event_id)
        if success:
            tg_user = get_user(user.id)
            if tg_user:
                tg_user.events_cancelled += 1
                tg_user.save()
            text = f"Событие {event_id} удалено."
        else:
            text = f"Событие с номером {event_id} не найдено или не принадлежит вам."
        update.message.reply_text(text)
    except ValueError:
        update.message.reply_text("ID события должно быть числом.")
    except Exception as e:
        update.message.reply_text(f"При удалении произошла ошибка: {e}")


def event_show_all_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        events = calendar.get_all_events(user.id)
        if events:
            lines = [f"№{e['id']}: {e['name']} — {e['date']} {e['time']}" for e in events]
            text = "Ваши события:\n" + "\n".join(lines)
        else:
            text = "У вас пока нет событий."
        update.message.reply_text(text)
    except Exception as e:
        update.message.reply_text(f"При получении списка событий произошла ошибка: {e}")


# --- Логика встреч ---

meeting_context = {}


def is_user_free(telegram_id, meeting_date, meeting_time):
    existing = Meeting.objects.filter(
        participant_id=telegram_id,
        date=meeting_date,
        time=meeting_time,
        status__in=['pending', 'confirmed']
    )
    return not existing.exists()


def invite_meeting(update, context):
    user = update.effective_user
    meeting_context[user.id] = {"step": "title"}
    update.message.reply_text("Создание встречи.\nВведите название встречи:")


def meeting_message_handler(update, context):
    user = update.effective_user
    if user.id not in meeting_context:
        return False

    ctx = meeting_context[user.id]
    text = update.message.text

    if ctx["step"] == "title":
        ctx["title"] = text
        ctx["step"] = "participant"
        update.message.reply_text("Введите Telegram ID участника (число):")
        return True

    if ctx["step"] == "participant":
        try:
            participant_id = int(text)
        except ValueError:
            update.message.reply_text("Нужно ввести число. Попробуйте снова:")
            return True
        ctx["participant_id"] = participant_id
        ctx["step"] = "date"
        update.message.reply_text("Введите дату встречи (ГГГГ-ММ-ДД):")
        return True

    if ctx["step"] == "date":
        try:
            meeting_date = datetime.datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            update.message.reply_text("Неверный формат. Пример: 2025-01-15")
            return True
        ctx["date"] = meeting_date
        ctx["step"] = "time"
        update.message.reply_text("Введите время встречи (ЧЧ:ММ):")
        return True

    if ctx["step"] == "time":
        try:
            meeting_time = datetime.datetime.strptime(text, "%H:%M").time()
        except ValueError:
            update.message.reply_text("Неверный формат. Пример: 14:30")
            return True
        ctx["time"] = meeting_time

        if not is_user_free(ctx["participant_id"], ctx["date"], ctx["time"]):
            update.message.reply_text("Участник занят в это время. Выберите другое время.")
            ctx["step"] = "date"
            update.message.reply_text("Введите новую дату (ГГГГ-ММ-ДД):")
            return True

        organizer_name = user.username or user.first_name or str(user.id)
        meeting = Meeting.objects.create(
            title=ctx["title"],
            date=ctx["date"],
            time=ctx["time"],
            organizer_id=user.id,
            organizer_name=organizer_name,
            participant_id=ctx["participant_id"],
            participant_name="",
            status='pending'
        )

        keyboard = [
            [
                InlineKeyboardButton("Подтвердить", callback_data=f"confirm_{meeting.id}"),
                InlineKeyboardButton("Отклонить", callback_data=f"decline_{meeting.id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            context.bot.send_message(
                chat_id=ctx["participant_id"],
                text=(
                    f"Вас приглашают на встречу!\n\n"
                    f"Название: {ctx['title']}\n"
                    f"Организатор: {organizer_name}\n"
                    f"Дата: {ctx['date']}\n"
                    f"Время: {ctx['time']}\n\n"
                    f"Подтверждаете или отклоняете?"
                ),
                reply_markup=reply_markup
            )
            update.message.reply_text(
                f"Приглашение отправлено пользователю {ctx['participant_id']}."
            )
        except Exception as e:
            update.message.reply_text(
                f"Не удалось отправить приглашение. "
                f"Возможно, пользователь не запускал бота. Ошибка: {e}"
            )

        del meeting_context[user.id]
        return True

    return False


def meeting_callback_handler(update, context):
    query = update.callback_query
    query.answer()

    data = query.data
    action, meeting_id = data.split("_")
    meeting_id = int(meeting_id)

    try:
        meeting = Meeting.objects.get(id=meeting_id)
    except Meeting.DoesNotExist:
        query.edit_message_text("Встреча не найдена.")
        return

    if action == "confirm":
        meeting.status = 'confirmed'
        meeting.save()
        query.edit_message_text("Вы подтвердили встречу!")
        try:
            context.bot.send_message(
                chat_id=meeting.organizer_id,
                text=f"Участник подтвердил встречу «{meeting.title}» "
                     f"на {meeting.date} в {meeting.time}."
            )
        except Exception:
            pass

    elif action == "decline":
        meeting.status = 'cancelled'
        meeting.save()
        query.edit_message_text("Вы отклонили встречу.")
        try:
            context.bot.send_message(
                chat_id=meeting.organizer_id,
                text=f"Участник отклонил встречу «{meeting.title}» "
                     f"на {meeting.date} в {meeting.time}."
            )
        except Exception:
            pass


def my_meetings(update, context):
    user = update.effective_user
    meetings = Meeting.objects.filter(
        participant_id=user.id,
        status__in=['pending', 'confirmed']
    ).order_by('date', 'time')

    if not meetings:
        update.message.reply_text("У вас нет запланированных встреч.")
        return

    text = "Ваши встречи:\n\n"
    for m in meetings:
        status_emoji = {"pending": "\u23f3", "confirmed": "\u2705", "cancelled": "\u274c"}
        text += (
            f"{status_emoji.get(m.status, '•')} {m.title}\n"
            f"   Дата: {m.date}  Время: {m.time}\n"
            f"   Организатор: {m.organizer_name}\n"
            f"   Статус: {m.get_status_display()}\n\n"
        )
    update.message.reply_text(text)


def share_event_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        if len(context.args) == 0:
            update.message.reply_text("Используйте: /share_event <id>")
            return
        event_id = int(context.args[0])
        new_status = calendar.toggle_public(user.id, event_id)
        if new_status is None:
            update.message.reply_text("Событие не найдено или не принадлежит вам.")
        else:
            status = "публичным" if new_status else "приватным"
            update.message.reply_text(f"Событие №{event_id} стало {status}.")
    except ValueError:
        update.message.reply_text("ID события должно быть числом.")
    except Exception as e:
        update.message.reply_text(f"Ошибка: {e}")


def public_callback_handler(update, context):
    query = update.callback_query
    query.answer()

    data = query.data
    action, event_id = data.split("_")
    event_id = int(event_id)

    if action == "public":
        user = query.from_user
        new_status = calendar.toggle_public(user.id, event_id)
        if new_status is None:
            query.edit_message_text("Событие не найдено или не принадлежит вам.")
        else:
            status = "публичным" if new_status else "приватным"
            button_text = "Сделать приватным" if new_status else "Сделать публичным"
            keyboard = [[InlineKeyboardButton(
                button_text, callback_data=f"public_{event_id}"
            )]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            old_text = query.message.text
            public_str = "да" if new_status else "нет"
            import re
            new_text = re.sub(r"Публичное: .+", f"Публичное: {public_str}", old_text)
            query.edit_message_text(new_text, reply_markup=reply_markup)


def public_events_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    try:
        events = calendar.get_public_events(user.id)
        if not events:
            update.message.reply_text("Пока нет публичных событий от других пользователей.")
            return

        # Получаем имена авторов событий
        lines = []
        for ev in events:
            try:
                owner = TelegramUser.objects.get(telegram_id=ev["owner_id"])
                owner_name = owner.username or owner.first_name or "Аноним"
            except TelegramUser.DoesNotExist:
                owner_name = "Аноним"
            lines.append(
                f"№{ev['id']} — {ev['name']}\n"
                f"  Дата: {ev['date']}  Время: {ev['time']}\n"
                f"  Автор: {owner_name}"
            )

        text = "🌍 Публичные события других пользователей:\n\n" + "\n\n".join(lines)
        update.message.reply_text(text)
    except Exception as e:
        update.message.reply_text(f"Ошибка при получении публичных событий: {e}")


def text_handler(update, context):
    if meeting_message_handler(update, context):
        return


def export_events_handler(update, context):
    user = update.effective_user
    if not is_registered(user.id):
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    base_url = "http://127.0.0.1:8000/events/export/"
    csv_url = f"{base_url}?format=csv&telegram_id={user.id}"
    json_url = f"{base_url}?format=json&telegram_id={user.id}"

    keyboard = [
        [
            InlineKeyboardButton("Скачать в CSV", url=csv_url),
            InlineKeyboardButton("Скачать в JSON", url=json_url)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите формат выгрузки:", reply_markup=reply_markup)


# --- Инициализация и регистрация ---

def main():
    updater = Updater(token=API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('register', register_handler))
    dispatcher.add_handler(CommandHandler('login', login_handler))
    dispatcher.add_handler(CommandHandler('calendar', calendar_handler))
    dispatcher.add_handler(CommandHandler('my_stats', my_stats_handler))
    dispatcher.add_handler(CommandHandler('create_event', event_create_handler))
    dispatcher.add_handler(CommandHandler('read_event', event_read_handler))
    dispatcher.add_handler(CommandHandler('edit_event', event_edit_handler))
    dispatcher.add_handler(CommandHandler('delete_event', event_delete_handler))
    dispatcher.add_handler(CommandHandler('all_events', event_show_all_handler))
    dispatcher.add_handler(CommandHandler('public_events', public_events_handler))


    dispatcher.add_handler(CommandHandler('invite_meeting', invite_meeting))
    dispatcher.add_handler(CommandHandler('my_meetings', my_meetings))
    dispatcher.add_handler(CallbackQueryHandler(meeting_callback_handler, pattern=r"^(confirm|decline)_"))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    dispatcher.add_handler(CommandHandler('share_event', share_event_handler))
    dispatcher.add_handler(CallbackQueryHandler(public_callback_handler, pattern=r"^public_"))
    dispatcher.add_handler(CommandHandler('public_events', public_events_handler))

    dispatcher.add_handler(CommandHandler('export', export_events_handler))



    print("Бот запущен и ждёт команд...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
