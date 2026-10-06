import psycopg2


class Calendar:
    """Класс для работы с событиями через прямые SQL-запросы."""

    def __init__(self, conn):
        self.conn = conn

    def _execute(self, query, params=None, fetch=False):
        """Обёртка для выполнения SQL с авто-закрытием курсора."""
        with self.conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch == "one":
                return cursor.fetchone()
            if fetch == "all":
                return cursor.fetchall()
            self.conn.commit()
            return cursor.rowcount

    def create_event(self, telegram_id, event_name, event_date, event_time, event_details):
        row = self._execute(
            "INSERT INTO events (telegram_id, name, date, time, details) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id;",
            (telegram_id, event_name, event_date, event_time, event_details),
            fetch="one"
        )
        return row[0] if row else None

    def read_event(self, telegram_id, event_id):
        row = self._execute(
            "SELECT id, name, date, time, details, is_public FROM events "
            "WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id),
            fetch="one"
        )
        if row:
            return {
                "id": row[0], "name": row[1], "date": row[2],
                "time": row[3], "details": row[4], "is_public": row[5],
            }
        return None

    def edit_event(self, telegram_id, event_id, event_name=None, event_date=None,
                   event_time=None, event_details=None):
        updates, values = [], []
        for field, value in [("name", event_name), ("date", event_date),
                             ("time", event_time), ("details", event_details)]:
            if value is not None:
                updates.append(f"{field} = %s")
                values.append(value)

        if not updates:
            return False

        values.extend([event_id, telegram_id])
        rowcount = self._execute(
            f"UPDATE events SET {', '.join(updates)} "
            f"WHERE id = %s AND telegram_id = %s;",
            values
        )
        return rowcount > 0

    def delete_event(self, telegram_id, event_id):
        rowcount = self._execute(
            "DELETE FROM events WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id)
        )
        return rowcount > 0

    def get_all_events(self, telegram_id):
        rows = self._execute(
            "SELECT id, name, date, time FROM events "
            "WHERE telegram_id = %s ORDER BY date, time;",
            (telegram_id,),
            fetch="all"
        )
        return [
            {"id": r[0], "name": r[1], "date": r[2], "time": r[3]}
            for r in rows
        ]

    def toggle_public(self, telegram_id, event_id):
        row = self._execute(
            "SELECT is_public FROM events WHERE id = %s AND telegram_id = %s;",
            (event_id, telegram_id),
            fetch="one"
        )
        if not row:
            return None
        new_status = not row[0]
        self._execute(
            "UPDATE events SET is_public = %s WHERE id = %s AND telegram_id = %s;",
            (new_status, event_id, telegram_id)
        )
        return new_status

    def get_public_events(self, telegram_id, limit=20):
        rows = self._execute(
            "SELECT id, name, date, time, telegram_id FROM events "
            "WHERE is_public = TRUE AND telegram_id != %s "
            "ORDER BY date, time LIMIT %s;",
            (telegram_id, limit),
            fetch="all"
        )
        return [
            {"id": r[0], "name": r[1], "date": r[2],
             "time": r[3], "owner_id": r[4]}
            for r in rows
        ]
