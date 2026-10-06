import psycopg2
from secrets import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id serial PRIMARY KEY,
    name text NOT NULL,
    date date NOT NULL,
    time time NOT NULL,
    details text
);
""")
conn.commit()
cursor.close()
conn.close()

print("Таблица events создана.")
