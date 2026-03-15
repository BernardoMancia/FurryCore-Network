from database.db_manager import DatabaseManager
import sqlite3

db = DatabaseManager()
try:
    with db.get_connection() as conn:
        conn.execute("ALTER TABLE usuarios_sistema ADD COLUMN totp_secret TEXT;")
        print("Coluna totp_secret adicionada com sucesso.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("Coluna totp_secret já existe.")
    else:
        print(f"Erro ao adicionar coluna: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
