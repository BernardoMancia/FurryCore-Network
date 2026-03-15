from database.db_manager import DatabaseManager
import sqlite3
import os

db = DatabaseManager()
db_path = "base_cgrf.db"

# Como SQLite não tem DROP COLUMN simples em versões muito antigas ou exige recriação para manter constraints, 
# vamos deletar o banco e recriar (para testes locais é o mais limpo) ou usar ALTER.
# No SQLite 3.35.0+ existe DROP COLUMN. Vamos tentar primeiro o DROP.

try:
    with db.get_connection() as conn:
        conn.execute("ALTER TABLE cidadaos DROP COLUMN alinhamento;")
        print("Coluna alinhamento removida via DROP COLUMN.")
except sqlite3.OperationalError:
    print("Versão do SQLite não suporta DROP COLUMN ou coluna já removida. Backup e Recriação...")
    try:
        with db.get_connection() as conn:
            # Pegar dados antigos
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cidadaos")
            col_names = [description[0] for description in cursor.description]
            if 'alinhamento' in col_names:
                # Recriar tabela é mais seguro para remover colunas em SQLite
                conn.execute("CREATE TABLE cidadaos_backup AS SELECT cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64 FROM cidadaos")
                conn.execute("DROP TABLE cidadaos")
                # Criar nova com schema correto
                with open("database/schema.sql", "r") as f:
                    conn.executescript(f.read())
                # Restaurar dados
                conn.execute("INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, is_valido, qrcode_base64, foto_base64) SELECT * FROM cidadaos_backup")
                conn.execute("DROP TABLE cidadaos_backup")
                print("Tabela recriada sem a coluna alinhamento.")
            else:
                print("Coluna alinhamento não encontrada.")
    except Exception as e:
        print(f"Erro na recriação: {e}")
