from django.contrib import admin
from .models import Event, TelegramUser, BotStatistics, Meeting


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id", "username", "first_name",
        "events_created", "events_edited", "events_cancelled",
        "registered_at",
    )
    list_filter = ("registered_at",)
    search_fields = ("telegram_id", "username", "first_name")
    ordering = ("-registered_at",)
    readonly_fields = ("registered_at",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "date", "time", "telegram_id")
    list_filter = ("date",)
    search_fields = ("name", "telegram_id")
    ordering = ("-id",)


@admin.register(BotStatistics)
class BotStatisticsAdmin(admin.ModelAdmin):
    list_display = ("date", "user_count", "event_count", "edited_events", "cancelled_events")
    ordering = ("-date",)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "time", "organizer_name", "participant_name", "status")
    list_filter = ("status", "date")
    search_fields = ("title", "organizer_name", "participant_name")
    ordering = ("-date", "-time")
