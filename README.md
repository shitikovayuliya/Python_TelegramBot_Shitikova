# Telegram-бот для управления событиями и встречами

**Учебный проект** — Telegram-бот с функцией календаря, созданный в рамках обучения.

## 👩‍💻 Автор

- **Имя:** Юлия Шитикова
- **GitHub:** [shitikovayuliya](https://github.com/shitikovayuliya)
- **Email:** shitikovayuliya@mail.ru

## 📋 Описание проекта

Telegram-бот для планирования событий и встреч с интеграцией Django Admin Panel. Позволяет пользователям создавать, редактировать, удалять события, отслеживать статистику и приглашать других пользователей на встречи.

## ✨ Возможности

- 👤 **Регистрация и авторизация** пользователей
- 📅 **Календарь событий** с группировкой по датам
- ➕ **Создание/редактирование/удаление** событий
- 📊 **Статистика** использования бота
- 🤝 **Система встреч** с приглашениями и подтверждением
- 🌍 **Публичные события** других пользователей
- 📤 **Экспорт** событий в CSV и JSON
- 🎨 **Интерактивное меню** с кнопками для быстрого доступа к функциям

## 🛠 Технологии

- **Python** 3.11+
- **python-telegram-bot** v13.15
- **Django** 4.2
- **PostgreSQL** 14
- **Docker** & **Docker Compose**
- **DRF** (Django Rest Framework)

## 🚀 Запуск проекта

### Требования

- Docker и Docker Compose
- Telegram Bot Token (от @BotFather)

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd Python_TelegramBot_Shitikova
   ```

2. Создайте файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Заполните переменные окружения в `.env`:
   - `TELEGRAM_BOT_TOKEN` — токен вашего бота
   - `DB_PASSWORD` — пароль для PostgreSQL
   - `SECRET_KEY` — ключ для Django

4. Запустите проект:
   ```bash
   docker-compose up --build
   ```

### Доступные сервисы

- **Telegram Bot** — запускается автоматически
- **Django Admin Panel** — http://localhost:8000/admin/
- **API** — http://localhost:8000/events/api/

## 🧪 Тесты

```bash
docker-compose exec web python -m pytest tests/ -v
```

## 📁 Структура проекта

```
├── admin_panel/          # Django приложение
│   ├── events/           # Модель событий, пользователей, встреч
│   └── admin_panel/      # Настройки Django
├── tests/                # Тесты pytest
├── bot.py                # Точка входа бота
├── bot_handlers.py       # Обработчики команд
├── bot_calendar.py       # Работа с календарем
├── bot_utils.py          # Вспомогательные функции
├── docker-compose.yml    # Конфигурация Docker
├── Dockerfile.bot        # Образ для бота
└── requirements.txt      # Зависимости Python
```

## ⚠️ Важно

Это **учебный проект**, созданный для демонстрации навыков работы с:
- Telegram Bot API
- Django ORM и Admin Panel
- Docker контейнеризацией
- PostgreSQL базой данных

Не используйте в продакшене без доработки безопасности!

## 📄 Лицензия

Учебный проект.
