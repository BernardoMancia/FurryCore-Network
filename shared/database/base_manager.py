import sqlite3
import os
import threading
from contextlib import contextmanager


class BaseDatabaseManager:
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, db_path, schema_path=None):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_directory()
        if schema_path:
            self._init_schema(schema_path)
        self._configure_pragmas()

    def _ensure_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _configure_pragmas(self):
        with self.get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")

    def _init_schema(self, schema_path):
        if os.path.exists(schema_path):
            with self.get_connection() as conn:
                with open(schema_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
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

    def execute_many(self, query, params_list):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def table_exists(self, table_name):
        result = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
            fetchone=True,
        )
        return result is not None

    def get_tables(self):
        rows = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            fetchall=True,
        )
        return [r["name"] for r in rows]

    def get_table_columns(self, table_name):
        if table_name not in self.get_tables():
            raise ValueError(f"Table '{table_name}' does not exist")
        with self.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            return cursor.fetchall()
