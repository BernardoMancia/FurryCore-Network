import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = r'f:\Projetos\Cadastro-e-Gestão-de-Registro-Furry\apps\pawsteps\database\pawsteps.db'

def setup_test_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Garantir que exista um usuário admin/sistema
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    if not admin:
        pwd_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, display_name, email, password_hash, status) VALUES (?, ?, ?, ?, ?)",
                       ('admin', 'Administrador', 'admin@furrycore.net', pwd_hash, 'ATIVO'))
        admin_id = cursor.lastrowid
    else:
        admin_id = admin[0]

    # 2. Limpar eventos existentes
    cursor.execute("DELETE FROM events")
    
    # 3. Inserir eventos de teste
    events = [
        (admin_id, "Brasil FurFest", "A maior convenção furry do Brasil.", "Santos", "Brasil", 2026, 0, "https://brasilfurfest.com.br", 1),
        (admin_id, "Brasil FurFest", "Edição memorável de Santos.", "Santos", "Brasil", 2025, 0, "https://brasilfurfest.com.br", 1),
        (admin_id, "Eurofurence", "A maior convenção da Europa.", "Hamburg", "Alemanha", 2026, 0, "https://eurofurence.org", 1),
        (admin_id, "Anthrocon", "A icônica convenção em Pittsburgh.", "Pittsburgh", "EUA", 2026, 0, "https://anthrocon.org", 1),
        (admin_id, "Meetup São Paulo", "Encontro mensal no Parque do Ibirapuera.", "São Paulo", "Brasil", 2026, 0, None, 1),
        (admin_id, "After Party NSFW", "Evento restrito pós-con (Exemplo).", "Santos", "Brasil", 2026, 1, None, 1)
    ]
    
    cursor.executemany("""
        INSERT INTO events (creator_id, name, description, city, country, year, is_nsfw, social_link, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, events)
    
    conn.commit()
    conn.close()
    print("Dados de teste configurados com sucesso!")

if __name__ == "__main__":
    setup_test_data()
