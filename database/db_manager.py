import sqlite3
import os
from contextlib import contextmanager

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = os.getenv("DB_PATH", "base_cgrf.db")
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        schema_path = os.path.join("database", "schema.sql")
        if os.path.exists(schema_path):
            with self.get_connection() as conn:
                with open(schema_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_query(self, query, params=(), fetchone=False, fetchall=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            return cursor.lastrowid
