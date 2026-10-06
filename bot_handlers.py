import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from events.models import TelegramUser, Meeting
from bot_utils import (
    require_registration, handle_errors, parse_event_id,
    get_owner_name, group_events_by_date, format_events_text,
    format_public_events_text,
)


# --- Управление пользователями ---

def register_user(telegram_id, username, first_name=""):
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username or "", "first_name": first_name or ""}
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


# --- Командные сообщения ---

COMMANDS_HELP = (
    "Доступные команды:\n"
    "/register — повторная регистрация\n"
    "/login — вход в личный кабинет\n"
    "/calendar — мой календарь\n"
    "/create_event <название> — создать событие\n"
    "/read_event <id> — посмотреть событие\n"
    "/edit_event <id> <новое название> — редактировать\n"
    "/delete_event <id> — удалить событие\n"
    "/all_events — все ваши события\n"
    "/my_stats — моя статистика\n"
    "/invite_meeting — пригласить на встречу\n"
    "/my_meetings — мои встречи\n"
    "/share_event <id> — сделать событие публичным/приватным\n"
    "/public_events — публичные события\n"
    "/export — выгрузить события в CSV или JSON\n"
)


# --- Обработчики команд ---

def start_handler(update, context):
    user = update.effective_user
    if TelegramUser.objects.filter(telegram_id=user.id).exists():
        update.message.reply_text(
            f"Привет, {user.first_name}! Вы уже зарегистрированы.\n" + COMMANDS_HELP
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
    if not tg_user:
        update.message.reply_text("Вы ещё не зарегистрированы. Используйте /register.")
        return

    update.message.reply_text(
        f"Вы вошли в личный кабинет.\n"
        f"ID: {tg_user.telegram_id}\n"
        f"Имя: {tg_user.username or tg_user.first_name}\n"
        f"Событий создано: {tg_user.events_created}\n"
        f"Событий отредактировано: {tg_user.events_edited}\n"
        f"Событий удалено: {tg_user.events_cancelled}\n\n"
        f"Команды:\n/calendar — мой календарь\n/my_stats — моя статистика"
    )


def calendar_handler(update, context, calendar):
    user = update.effective_user
    from bot_utils import require_registration

    if not TelegramUser.objects.filter(telegram_id=user.id).exists():
        update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    events = calendar.get_all_events(user.id)
    text = format_events_text(group_events_by_date(events), "📅 Ваш календарь:")
    if not text:
        text = "📅 Ваш календарь пуст. Создайте событие: /create_event <название>\n\n"

    public_events = calendar.get_public_events(user.id)
    public_text = format_public_events_text(public_events)
    if public_text:
        text += public_text

    update.message.reply_text(text)


@require_registration
@handle_errors
def my_stats_handler(update, context):
    tg_user = get_user(update.effective_user.id)
    update.message.reply_text(
        f"📊 Ваша статистика:\n\n"
        f"Событий создано: {tg_user.events_created}\n"
        f"Событий отредактировано: {tg_user.events_edited}\n"
        f"Событий удалено: {tg_user.events_cancelled}\n"
    )


@require_registration
@handle_errors
def event_create_handler(update, context, calendar):
    if not context.args:
        update.message.reply_text("Укажите название события: /create_event <название>")
        return

    event_name = " ".join(context.args).strip()
    if not event_name:
        update.message.reply_text("Название не может быть пустым.")
        return

    event_id = calendar.create_event(
        update.effective_user.id, event_name, "2026-10-06", "14:00", "Описание события"
    )
    tg_user = get_user(update.effective_user.id)
    if tg_user:
        tg_user.events_created += 1
        tg_user.save()

    update.message.reply_text(f"Событие «{event_name}» создано и имеет номер {event_id}.")


@require_registration
@handle_errors
def event_read_handler(update, context, calendar):
    event_id = parse_event_id(context.args)
    event = calendar.read_event(update.effective_user.id, event_id)
    if not event:
        update.message.reply_text(f"Событие с номером {event_id} не найдено.")
        return

    public_status = "да" if event.get("is_public") else "нет"
    text = (
        f"Событие №{event['id']}\n"
        f"Название: {event['name']}\n"
        f"Дата: {event['date']}\n"
        f"Время: {event['time']}\n"
        f"Описание: {event['details']}\n"
        f"Публичное: {public_status}"
    )
    button_text = "Сделать приватным" if event.get("is_public") else "Сделать публичным"
    keyboard = [[InlineKeyboardButton(button_text, callback_data=f"public_{event_id}")]]
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


@require_registration
@handle_errors
def event_edit_handler(update, context, calendar):
    event_id = parse_event_id(context.args)
    event_name = " ".join(context.args[1:]) if len(context.args) > 1 else None
    success = calendar.edit_event(update.effective_user.id, event_id, event_name=event_name)

    if success:
        tg_user = get_user(update.effective_user.id)
        if tg_user:
            tg_user.events_edited += 1
            tg_user.save()
        update.message.reply_text(f"Событие {event_id} отредактировано.")
    else:
        update.message.reply_text(f"Событие с номером {event_id} не найдено или не принадлежит вам.")


@require_registration
@handle_errors
def event_delete_handler(update, context, calendar):
    event_id = parse_event_id(context.args)
    success = calendar.delete_event(update.effective_user.id, event_id)

    if success:
        tg_user = get_user(update.effective_user.id)
        if tg_user:
            tg_user.events_cancelled += 1
            tg_user.save()
        update.message.reply_text(f"Событие {event_id} удалено.")
    else:
        update.message.reply_text(f"Событие с номером {event_id} не найдено или не принадлежит вам.")


@require_registration
@handle_errors
def event_show_all_handler(update, context, calendar):
    events = calendar.get_all_events(update.effective_user.id)
    if events:
        lines = [f"№{e['id']}: {e['name']} — {e['date']} {e['time']}" for e in events]
        update.message.reply_text("Ваши события:\n" + "\n".join(lines))
    else:
        update.message.reply_text("У вас пока нет событий.")


@require_registration
@handle_errors
def public_events_handler(update, context, calendar):
    events = calendar.get_public_events(update.effective_user.id)
    if not events:
        update.message.reply_text("Пока нет публичных событий от других пользователей.")
        return

    lines = []
    for ev in events:
        owner_name = get_owner_name(ev["owner_id"])
        lines.append(
            f"№{ev['id']} — {ev['name']}\n"
            f"  Дата: {ev['date']}  Время: {ev['time']}\n"
            f"  Автор: {owner_name}"
        )
    update.message.reply_text("🌍 Публичные события других пользователей:\n\n" + "\n\n".join(lines))


@require_registration
@handle_errors
def share_event_handler(update, context, calendar):
    event_id = parse_event_id(context.args)
    new_status = calendar.toggle_public(update.effective_user.id, event_id)
    if new_status is None:
        update.message.reply_text("Событие не найдено или не принадлежит вам.")
    else:
        status = "публичным" if new_status else "приватным"
        update.message.reply_text(f"Событие №{event_id} стало {status}.")


@require_registration
def export_events_handler(update, context):
    user = update.effective_user
    base_url = "http://127.0.0.1:8000/events/export/"
    keyboard = [[
        InlineKeyboardButton("Скачать в CSV", url=f"{base_url}?format=csv&telegram_id={user.id}"),
        InlineKeyboardButton("Скачать в JSON", url=f"{base_url}?format=json&telegram_id={user.id}")
    ]]
    update.message.reply_text("Выберите формат выгрузки:", reply_markup=InlineKeyboardMarkup(keyboard))


# --- Callback-обработчики ---

def public_callback_handler(update, context, calendar):
    query = update.callback_query
    query.answer()

    _, event_id = query.data.split("_")
    event_id = int(event_id)

    user = query.from_user
    new_status = calendar.toggle_public(user.id, event_id)
    if new_status is None:
        query.edit_message_text("Событие не найдено или не принадлежит вам.")
        return

    button_text = "Сделать приватным" if new_status else "Сделать публичным"
    keyboard = [[InlineKeyboardButton(button_text, callback_data=f"public_{event_id}")]]
    old_text = query.message.text
    public_str = "да" if new_status else "нет"
    new_text = re.sub(r"Публичное: .+", f"Публичное: {public_str}", old_text)
    query.edit_message_text(new_text, reply_markup=InlineKeyboardMarkup(keyboard))


# --- Логика встреч ---

meeting_context = {}


def is_user_free(telegram_id, meeting_date, meeting_time):
    return not Meeting.objects.filter(
        participant_id=telegram_id,
        date=meeting_date,
        time=meeting_time,
        status__in=['pending', 'confirmed']
    ).exists()


MEETING_STEPS = ["title", "participant", "date", "time"]


def invite_meeting(update, context):
    user = update.effective_user
    meeting_context[user.id] = {"step": "title"}
    update.message.reply_text("Создание встречи.\nВведите название встречи:")


def _parse_meeting_input(step, text):
    """Парсит ввод пользователя на каждом шаге. Возвращает (value, error_msg)."""
    if step == "title":
        return text, None
    if step == "participant":
        try:
            return int(text), None
        except ValueError:
            return None, "Нужно ввести число. Попробуйте снова:"
    if step == "date":
        try:
            return datetime.datetime.strptime(text, "%Y-%m-%d").date(), None
        except ValueError:
            return None, "Неверный формат. Пример: 2025-01-15"
    if step == "time":
        try:
            return datetime.datetime.strptime(text, "%H:%M").time(), None
        except ValueError:
            return None, "Неверный формат. Пример: 14:30"
    return None, None


def _process_meeting_step(update, context, ctx, text):
    """Обрабатывает один шаг создания встречи. Возвращает True если шаг завершён."""
    step = ctx["step"]
    value, error = _parse_meeting_input(step, text)

    if error:
        update.message.reply_text(error)
        return True

    ctx[step] = value
    next_step = MEETING_STEPS[MEETING_STEPS.index(step) + 1] if step != "time" else None

    if next_step:
        prompts = {
            "participant": "Введите Telegram ID участника (число):",
            "date": "Введите дату встречи (ГГГГ-ММ-ДД):",
            "time": "Введите время встречи (ЧЧ:ММ):",
        }
        ctx["step"] = next_step
        update.message.reply_text(prompts[next_step])
        return True

    # Финальный шаг — создаём встречу
    return _finalize_meeting(update, context, ctx)


def _finalize_meeting(update, context, ctx):
    """Создаёт встречу и отправляет приглашение."""
    user = update.effective_user

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

    keyboard = [[
        InlineKeyboardButton("Подтвердить", callback_data=f"confirm_{meeting.id}"),
        InlineKeyboardButton("Отклонить", callback_data=f"decline_{meeting.id}"),
    ]]

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
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        update.message.reply_text(f"Приглашение отправлено пользователю {ctx['participant_id']}.")
    except Exception as e:
        update.message.reply_text(
            f"Не удалось отправить приглашение. "
            f"Возможно, пользователь не запускал бота. Ошибка: {e}"
        )

    del meeting_context[user.id]
    return True


def meeting_message_handler(update, context):
    user = update.effective_user
    if user.id not in meeting_context:
        return False
    return _process_meeting_step(update, context, meeting_context[user.id], update.message.text)


def meeting_callback_handler(update, context):
    query = update.callback_query
    query.answer()

    action, meeting_id = query.data.split("_")
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
        _notify_organizer(context, meeting, "подтвердил")
    elif action == "decline":
        meeting.status = 'cancelled'
        meeting.save()
        query.edit_message_text("Вы отклонили встречу.")
        _notify_organizer(context, meeting, "отклонил")


def _notify_organizer(context, meeting, action):
    """Отправляет уведомление организатору о решении участника."""
    try:
        context.bot.send_message(
            chat_id=meeting.organizer_id,
            text=f"Участник {action} встречу «{meeting.title}» "
                 f"на {meeting.date} в {meeting.time}."
        )
    except Exception:
        pass


STATUS_EMOJI = {"pending": "⏳", "confirmed": "✅", "cancelled": "❌"}


def my_meetings(update, context):
    user = update.effective_user
    meetings = Meeting.objects.filter(
        participant_id=user.id,
        status__in=['pending', 'confirmed']
    ).order_by('date', 'time')

    if not meetings:
        update.message.reply_text("У вас нет запланированных встреч.")
        return

    lines = ["Ваши встречи:\n"]
    for m in meetings:
        emoji = STATUS_EMOJI.get(m.status, "•")
        lines.append(
            f"{emoji} {m.title}\n"
            f"   Дата: {m.date}  Время: {m.time}\n"
            f"   Организатор: {m.organizer_name}\n"
            f"   Статус: {m.get_status_display()}\n"
        )
    update.message.reply_text("\n".join(lines))


def text_handler(update, context):
    meeting_message_handler(update, context)
