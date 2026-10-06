import psycopg2
from secrets import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = conn.cursor()

# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id bigint PRIMARY KEY,
    username text,
    registered_at timestamp DEFAULT CURRENT_TIMESTAMP
);
""")

# Пересоздаём таблицу events с user_id
cursor.execute("DROP TABLE IF EXISTS events;")
cursor.execute("""
CREATE TABLE events (
    id serial PRIMARY KEY,
    telegram_id bigint NOT NULL REFERENCES users(telegram_id),
    name text NOT NULL,
    date date NOT NULL,
    time time NOT NULL,
    details text
);
""")

conn.commit()
cursor.close()
conn.close()

print("Таблицы users и events созданы.")
