import sqlite3
import os

# Caminho DEFINITIVO
db_path = "f:/Projetos/Cadastro-e-Gestão-de-Registro-Furry/apps/cgrf/database/base_cgrf.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Erro: Banco não encontrado em {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Adicionar colunas se não existirem
    columns_to_add = ["cidade", "idiomas", "pais"]
    
    for col in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE cidadaos ADD COLUMN {col} TEXT")
            print(f"Coluna '{col}' adicionada.")
        except sqlite3.OperationalError:
            print(f"Coluna '{col}' já existe.")

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso.")

if __name__ == "__main__":
    migrate()
