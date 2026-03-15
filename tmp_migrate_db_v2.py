import sqlite3
import os

# Caminho NOVO e DEFINITIVO
db_path = "f:/Projetos/Cadastro-e-Gestão-de-Registro-Furry/apps/cgrf/database/base_cgrf.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Erro: Banco não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Adicionar colunas se não existirem
    try:
        cursor.execute("ALTER TABLE cidadaos ADD COLUMN cidade TEXT")
        print("Coluna 'cidade' adicionada.")
    except sqlite3.OperationalError:
        print("Coluna 'cidade' já existe.")

    try:
        cursor.execute("ALTER TABLE cidadaos ADD COLUMN idiomas TEXT")
        print("Coluna 'idiomas' adicionada.")
    except sqlite3.OperationalError:
        print("Coluna 'idiomas' já existe.")

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso no novo path.")

if __name__ == "__main__":
    migrate()
