import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from shared.database.base_manager import BaseDatabaseManager


class DatabaseManager(BaseDatabaseManager):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.getenv("DB_PATH", os.path.join(base_dir, "database", "base_cgrf.db"))
            schema_path = os.path.join(base_dir, "database", "schema.sql")
            instance = super(BaseDatabaseManager, cls).__new__(cls)
            instance.__init__(db_path, schema_path)
            cls._instance = instance
        return cls._instance

    def __init__(self, *args, **kwargs):
        if hasattr(self, "db_path"):
            return
        if args:
            super().__init__(*args, **kwargs)
