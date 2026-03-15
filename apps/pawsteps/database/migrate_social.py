import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'pawsteps.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Iniciando migração do PawSteps DB...")

# Novas tabelas de interações
queries = [
    """
    CREATE TABLE IF NOT EXISTS post_likes (
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS post_saves (
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS post_reposts (
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )
    """
]

for q in queries:
    cursor.execute(q)
    print("Tabela criada/verificada.")

# Adicionar colunas na tabela posts, ignorando se já existir
try:
    cursor.execute("ALTER TABLE posts ADD COLUMN reply_to_post_id INTEGER REFERENCES posts(id)")
    print("Coluna reply_to_post_id adicionada a posts.")
except sqlite3.OperationalError:
    print("Coluna reply_to_post_id já existe.")

try:
    cursor.execute("ALTER TABLE posts ADD COLUMN location TEXT")
    print("Coluna location adicionada a posts.")
except sqlite3.OperationalError:
    print("Coluna location já existe.")
    
try:
    cursor.execute("ALTER TABLE posts ADD COLUMN is_repost BOOLEAN DEFAULT 0")
    print("Coluna is_repost adicionada a posts.")
except sqlite3.OperationalError:
    print("Coluna is_repost já existe.")
    
try:
    cursor.execute("ALTER TABLE posts ADD COLUMN original_post_id INTEGER REFERENCES posts(id)")
    print("Coluna original_post_id adicionada a posts.")
except sqlite3.OperationalError:
    print("Coluna original_post_id já existe.")

# Adicionar colunas na tabela users
try:
    cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
    print("Coluna phone_number adicionada a users.")
except sqlite3.OperationalError:
    print("Coluna phone_number já existe.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0")
    print("Coluna mfa_enabled adicionada a users.")
except sqlite3.OperationalError:
    print("Coluna mfa_enabled já existe.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_cover_url TEXT")
    print("Coluna profile_cover_url adicionada a users.")
except sqlite3.OperationalError:
    print("Coluna profile_cover_url já existe.")

conn.commit()
conn.close()
print("Migração concluída com sucesso!")
