import sqlite3
import os

db_path = r'f:\Projetos\Cadastro-e-Gestão-de-Registro-Furry\apps\pawsteps\database\pawsteps.db'

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN title TEXT")
        print("Coluna 'title' adicionada na tabela posts.")
    except sqlite3.OperationalError as e:
        print("Erro (provavelmente a coluna já existe):", e)
        
    # Ensure media_url exists (it does in schema, but just in case)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate()
