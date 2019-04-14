import sqlite3


class Database:
    def __init__(self, filename):
        self.filename = filename
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.filename)
        except sqlite3.Error:
            print("Error connecting to sqlite database")

    def create_table(self, table, rows, check_first=False):
        if self.conn:
            if check_first is True:
                query = f"CREATE TABLE IF NOT EXISTS {table} ({rows})"
            else:
                query = f"CREATE TABLE IF NOT EXISTS {table} ({rows})"
            self.conn.execute(query)

    def insert(self, table, columns, values, args=None, replace=False):
        if self.conn:
            if replace is True:
                query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({values})"
            else:
                query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
            self.conn.execute(query, args or tuple())
            self._save()

    def delete(self, table, where, args=None):
        if self.conn:
            query = f"DELETE FROM {table} WHERE {where}"
            self.conn.execute(query, args or tuple())
            self._save()


    def select(self, columns, table, where=None, args=None, limit=0):
        if self.conn:
            query = f"SELECT {columns} FROM {table}"
            if where:
                query += f" WHERE {where}"
            rows = self.conn.execute(query, args or tuple()).fetchall()
            return rows[len(rows) - limit if limit else 0:]

    def close(self):
        if self.conn:
            self._save()
            self.cursor.close()
            self.conn.close()

    def _save(self):
        if self.conn:
            self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self):
        if self.conn:
            self.close()
