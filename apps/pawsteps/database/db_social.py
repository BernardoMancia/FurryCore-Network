import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from shared.database.base_manager import BaseDatabaseManager


class SocialDatabaseManager(BaseDatabaseManager):
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), "pawsteps.db")
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        super().__init__(db_path, schema_path if not os.path.exists(db_path) else None)

        if not self.table_exists("users"):
            self._init_schema(schema_path)
