import re
import functools
from events.models import TelegramUser


def require_registration(handler):
    """Декоратор: проверяет, что пользователь зарегистрирован."""
    @functools.wraps(handler)
    def wrapper(update, context):
        user = update.effective_user
        if not TelegramUser.objects.filter(telegram_id=user.id).exists():
            update.message.reply_text("Сначала зарегистрируйтесь: /register")
            return
        return handler(update, context)
    return wrapper


def handle_errors(handler):
    """Декоратор: перехватывает ошибки и отправляет сообщение пользователю."""
    @functools.wraps(handler)
    def wrapper(update, context):
        try:
            return handler(update, context)
        except ValueError:
            update.message.reply_text("ID события должно быть числом.")
        except Exception as e:
            update.message.reply_text(f"Произошла ошибка: {e}")
    return wrapper


def parse_event_id(args):
    """Парсит ID события из аргументов команды. Бросает ValueError при ошибке."""
    if not args:
        raise ValueError("Аргумент не передан")
    return int(args[0])


def get_owner_name(owner_id):
    """Возвращает имя пользователя по telegram_id или 'Аноним'."""
    try:
        owner = TelegramUser.objects.get(telegram_id=owner_id)
        return owner.username or owner.first_name or "Аноним"
    except TelegramUser.DoesNotExist:
        return "Аноним"


def group_events_by_date(events):
    """Группирует список событий по дате. Возвращает dict {date_str: [events]}."""
    grouped = {}
    for e in events:
        date_str = str(e["date"])
        grouped.setdefault(date_str, []).append(e)
    return grouped


def format_events_text(grouped, title="📅 Календарь:"):
    """Форматирует сгруппированные события в текстовое сообщение."""
    if not grouped:
        return None
    lines = [title, ""]
    for date_str in sorted(grouped.keys()):
        lines.append(f"📌 {date_str}")
        for e in grouped[date_str]:
            lines.append(f"   ⏰ {e['time']} — {e['name']} (№{e['id']})")
        lines.append("")
    return "\n".join(lines)


def format_public_events_text(events):
    """Форматирует публичные события с именами авторов."""
    if not events:
        return None
    grouped = group_events_by_date(events)
    lines = ["🌍 Общие события:", ""]
    for date_str in sorted(grouped.keys()):
        lines.append(f"📌 {date_str}")
        for e in grouped[date_str]:
            owner_name = get_owner_name(e["owner_id"])
            lines.append(f"   ⏰ {e['time']} — {e['name']} (от {owner_name})")
        lines.append("")
    return "\n".join(lines)
