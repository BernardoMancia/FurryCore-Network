import sqlite3
import os

db_path = "base_cgrf.db"

def migrate_status():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna status já existe
        cursor.execute("PRAGMA table_info(usuarios_sistema)")
        cols = [c[1] for c in cursor.fetchall()]
        
        if 'status' not in cols:
            print("Adicionando coluna 'status' à tabela usuarios_sistema...")
            cursor.execute("ALTER TABLE usuarios_sistema ADD COLUMN status TEXT DEFAULT 'ATIVO'")
            # Usuários antigos são marcados como ATIVO por padrão
            conn.commit()
            print("Migração concluída.")
        else:
            print("Coluna 'status' já existe.")
            
    except Exception as e:
        print(f"Erro na migração: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_status()
