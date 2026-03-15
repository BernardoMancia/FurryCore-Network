import sqlite3
import os

# Caminho RELATIVO para compatibilidade VPS/Local
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "apps", "cgrf", "database", "base_cgrf.db")
if not os.path.exists(db_path):
    # Tenta caminho do container se estiver em ambiente Docker
    db_path = "/app/database/base_cgrf.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Erro: Banco não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Adicionar coluna 'status' na tabela 'usuarios_sistema' se não existir
    try:
        cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN status TEXT NOT NULL DEFAULT 'ATIVO'")
        print("Coluna 'status' adicionada à tabela 'usuarios_sistema'.")
    except sqlite3.OperationalError:
        print("Coluna 'status' já existe na tabela 'usuarios_sistema' ou erro operacional.")

    conn.commit()
    conn.close()
    print("Migração v4 (status column) concluída.")

if __name__ == "__main__":
    migrate()
