import sqlite3
import os

db_path = "base_cgrf.db"

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Iniciando migração...")
    
    # 1. Adicionar campos_sob_revisao em cidadaos
    try:
        cursor.execute("ALTER TABLE cidadaos ADD COLUMN campos_sob_revisao TEXT;")
        print("Coluna campos_sob_revisao adicionada à tabela cidadaos.")
    except sqlite3.OperationalError:
        print("Coluna campos_sob_revisao já existe ou erro na alteração.")

    # 2. Reestruturar solicitacoes_privacidade
    # Vamos renomear a antiga, criar a nova e migrar se houver dados
    try:
        cursor.execute("ALTER TABLE solicitacoes_privacidade RENAME TO solicitacoes_privacidade_old;")
        
        cursor.execute("""
            CREATE TABLE solicitacoes_privacidade (
                id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
                cnf_solicitante TEXT NOT NULL,
                tipo_acao TEXT NOT NULL CHECK (tipo_acao IN ('ALTERAR', 'REMOVER')),
                detalhes_json TEXT,
                status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'APROVADO', 'REJEITADO')),
                motivo_rejeicao TEXT,
                data_solicitacao TEXT NOT NULL,
                FOREIGN KEY (cnf_solicitante) REFERENCES cidadaos(cnf) ON DELETE CASCADE
            );
        """)
        
        # Tentar migrar dados básicos se existirem
        cursor.execute("""
            INSERT INTO solicitacoes_privacidade (id_solicitacao, cnf_solicitante, tipo_acao, status, data_solicitacao)
            SELECT id_solicitacao, cnf_solicitante, 'REMOVER', status, data_solicitacao
            FROM solicitacoes_privacidade_old;
        """)
        
        cursor.execute("DROP TABLE solicitacoes_privacidade_old;")
        print("Tabela solicitacoes_privacidade reestruturada com sucesso.")
    except Exception as e:
        print(f"Erro ao reestruturar solicitacoes_privacidade: {e}")
        # Se falhou porque a tabela old não existe, talvez já tenha sido migrado ou a nova estrutura já exista
        pass

    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
