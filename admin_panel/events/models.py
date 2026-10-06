from django.db import models
from datetime import date


class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    details = models.TextField(blank=True, null=True)
    telegram_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'events'

    def __str__(self):
        return self.name


class TelegramUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    events_created = models.PositiveIntegerField(default=0)
    events_edited = models.PositiveIntegerField(default=0)
    events_cancelled = models.PositiveIntegerField(default=0)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.username or self.first_name} ({self.telegram_id})"


class BotStatistics(models.Model):
    date = models.DateField(unique=True)
    user_count = models.PositiveIntegerField(default=0)
    event_count = models.PositiveIntegerField(default=0)
    edited_events = models.PositiveIntegerField(default=0)
    cancelled_events = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Bot Statistics"
        ordering = ["-date"]

    def __str__(self):
        return f"Статистика за {self.date}"


class Meeting(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидается'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
    ]

    title = models.CharField("Название встречи", max_length=255)
    date = models.DateField("Дата")
    time = models.TimeField("Время")
    organizer_id = models.BigIntegerField("ID организатора")
    organizer_name = models.CharField("Имя организатора", max_length=255, blank=True)
    participant_id = models.BigIntegerField("ID участника")
    participant_name = models.CharField("Имя участника", max_length=255, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Встреча"
        verbose_name_plural = "Встречи"
        ordering = ["-date", "-time"]

    def __str__(self):
        return f"{self.title} — {self.date} {self.time} ({self.get_status_display()})"
