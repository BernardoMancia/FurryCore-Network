-- FurryCore Network - Schema SQL

-- Tabela 1: cidadaos (O Cofre de Identidades)
CREATE TABLE IF NOT EXISTS cidadaos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnf TEXT UNIQUE NOT NULL,
    rgf TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    especie TEXT NOT NULL,
    regiao TEXT NOT NULL,
    email TEXT,
    data_emissao TEXT NOT NULL,
    data_expiracao TEXT NOT NULL,
    is_valido BOOLEAN DEFAULT 1,
    qrcode_base64 TEXT,
    foto_base64 TEXT,
    cidade TEXT,
    idiomas TEXT,
    pais TEXT,
    campos_sob_revisao TEXT -- JSON listando campos ocultos temporariamente
);

-- Tabela 2: usuarios_sistema (Controle de Acessos)
CREATE TABLE IF NOT EXISTS usuarios_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnf_vinculado TEXT,
    email TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    cargo TEXT NOT NULL CHECK (cargo IN ('ADMIN', 'ANALISTA', 'USUARIO')),
    status TEXT NOT NULL DEFAULT 'ATIVO',
    token_recuperacao TEXT,
    totp_secret TEXT,
    FOREIGN KEY (cnf_vinculado) REFERENCES cidadaos(cnf) ON DELETE SET NULL
);

-- Tabela 3: solicitacoes_privacidade (Tickets Internos)
CREATE TABLE IF NOT EXISTS solicitacoes_privacidade (
    id_solicitacao INTEGER PRIMARY KEY AUTOINCREMENT,
    cnf_solicitante TEXT NOT NULL,
    tipo_acao TEXT NOT NULL CHECK (tipo_acao IN ('ALTERAR', 'REMOVER')),
    detalhes_json TEXT, -- Dados novos ou campos a remover
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'APROVADO', 'REJEITADO')),
    motivo_rejeicao TEXT,
    data_solicitacao TEXT NOT NULL,
    FOREIGN KEY (cnf_solicitante) REFERENCES cidadaos(cnf) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cidadaos_email ON cidadaos(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios_sistema(email);
