import sqlite3
import os

db_path = r'f:\Projetos\Cadastro-e-Gestão-de-Registro-Furry\apps\pawsteps\database\pawsteps.db'

def insert_test_media():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Pegar dois eventos aprovados (ex: BFF)
    cursor.execute("SELECT id, year FROM events WHERE name = 'Brasil FurFest' LIMIT 2")
    events = cursor.fetchall()
    
    if not events:
        print("Adicione eventos BFF primeiro (rode insert_test_events.py se necessário).")
        return
        
    e1_id, e1_year = events[0]
    
    # Pegar o usuário admin (1) ou root
    cursor.execute("SELECT id FROM users LIMIT 1")
    user = cursor.fetchone()
    if not user: return
    u_id = user[0]
    
    # 2. Inserir Posts fakes (URLs estáticas falsas simulando imagens e vídeos)
    posts = [
        (u_id, 'Foto linda do evento!', 'Eu e meu amigo @luke lá no salão principal #furfest #brasil', 0, e1_id, 'https://picsum.photos/id/237/400/300'),
        (u_id, 'Party no Quarto', 'O after foi incrível! @furrydog', 1, e1_id, 'https://picsum.photos/id/1025/400/300')
    ]
    
    cursor.executemany("INSERT INTO posts (user_id, title, content, is_nsfw, event_id, media_url) VALUES (?, ?, ?, ?, ?, ?)", posts)
    
    conn.commit()
    conn.close()
    print("Mídias de teste inseridas com sucesso.")

if __name__ == '__main__':
    insert_test_media()
