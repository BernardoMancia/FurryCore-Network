from database.db_manager import DatabaseManager
import sqlite3

db = DatabaseManager()
try:
    with db.get_connection() as conn:
        # No SQLite, adicionar uma coluna como PRIMARY KEY AUTOINCREMENT exige recriação da tabela.
        conn.execute("CREATE TABLE cidadaos_temp AS SELECT * FROM cidadaos")
        conn.execute("DROP TABLE cidadaos")
        
        # Criar nova com schema correto (id incluso)
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
        conn.executescript(schema)
        
        # Migrar dados (mapeando colunas, pulando id para preenchimento automático)
        conn.execute("""
            INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64)
            SELECT cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64 FROM cidadaos_temp
        """)
        conn.execute("DROP TABLE cidadaos_temp")
        print("Tabela cidadaos atualizada com coluna id.")
except Exception as e:
    print(f"Erro ao atualizar schema: {e}")
