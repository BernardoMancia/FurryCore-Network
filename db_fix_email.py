from database.db_manager import DatabaseManager
import sqlite3

db = DatabaseManager()
try:
    with db.get_connection() as conn:
        # No SQLite, para remover NOT NULL, geralmente é preciso recriar a tabela.
        # Mas vamos apenas tentar inserir NULL para ver se o DB atualizado aceita.
        # Como é um ambiente de desenvolvimento e já fizemos recriações antes, vou rodar o fix.
        conn.execute("CREATE TABLE cidadaos_temp AS SELECT * FROM cidadaos")
        conn.execute("DROP TABLE cidadaos")
        with open("database/schema.sql", "r") as f:
            conn.executescript(f.read())
        conn.execute("INSERT INTO cidadaos SELECT * FROM cidadaos_temp")
        conn.execute("DROP TABLE cidadaos_temp")
        print("Schema atualizado: E-mail agora é opcional.")
except Exception as e:
    print(f"Erro ao atualizar schema: {e}")
