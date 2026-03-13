import sqlite3
import os

db_path = "base_cgrf.db"

def fix_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Verificar se id já existe
        cursor.execute("PRAGMA table_info(cidadaos)")
        cols = [c[1] for c in cursor.fetchall()]
        
        if 'id' in cols:
            print("Coluna 'id' já existe.")
            return

        print("Iniciando migração forçada...")
        
        # 2. Criar tabela temporária com os dados atuais
        cursor.execute("CREATE TABLE cidadaos_old AS SELECT * FROM cidadaos")
        
        # 3. Deletar tabela antiga
        cursor.execute("DROP TABLE cidadaos")
        
        # 4. Criar nova tabela com schema definitivo
        schema = """
        CREATE TABLE cidadaos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnf TEXT NOT NULL UNIQUE,
            rgf TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            regiao TEXT NOT NULL,
            email TEXT,
            data_emissao TEXT NOT NULL,
            data_expiracao TEXT NOT NULL,
            is_valido BOOLEAN DEFAULT 1,
            qrcode_base64 TEXT,
            foto_base64 TEXT
        );
        """
        cursor.execute(schema)
        
        # 5. Migrar dados mapeando colunas
        cursor.execute("""
            INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64)
            SELECT cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64 FROM cidadaos_old
        """)
        
        # 6. Limpar backup
        cursor.execute("DROP TABLE cidadaos_old")
        
        conn.commit()
        print("Banco de dados corrigido com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"ERRO CRÍTICO NA MIGRAÇÃO: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
