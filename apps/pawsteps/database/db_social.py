import sqlite3
import os

class SocialDatabaseManager:
    def __init__(self):
        # Caminho do banco social
        self.db_path = os.path.join(os.path.dirname(__file__), 'pawsteps.db')
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        if not os.path.exists(self.db_path):
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            conn = self._get_connection()
            conn.executescript(schema)
            conn.commit()
            conn.close()

    def execute_query(self, query, params=(), fetchone=False, fetchall=False):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetchone:
                res = cursor.fetchone()
            elif fetchall:
                res = cursor.fetchall()
            else:
                conn.commit()
                res = cursor.lastrowid
            return res
        finally:
            conn.close()
