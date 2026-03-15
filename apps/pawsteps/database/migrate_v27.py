import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'pawsteps.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Iniciando migração de preferências de privacidade...")

# Adicionar colunas de preferência na tabela users
try:
    cursor.execute("ALTER TABLE users ADD COLUMN view_nsfw BOOLEAN DEFAULT 0")
    print("Coluna view_nsfw adicionada.")
except sqlite3.OperationalError:
    print("Coluna view_nsfw já existe.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN share_location BOOLEAN DEFAULT 1")
    print("Coluna share_location adicionada.")
except sqlite3.OperationalError:
    print("Coluna share_location já existe.")

# Adicionar slug na tabela events para URLs limpas
try:
    cursor.execute("ALTER TABLE events ADD COLUMN slug TEXT")
    print("Coluna slug adicionada a events.")
except sqlite3.OperationalError:
    print("Coluna slug já existe.")

# Popular slugs iniciais baseados no nome
cursor.execute("SELECT id, name FROM events")
events = cursor.fetchall()
for eid, name in events:
    slug = name.lower().replace(' ', '-')
    cursor.execute("UPDATE events SET slug = ? WHERE id = ?", (slug, eid))

conn.commit()
conn.close()
print("Migração concluída!")
