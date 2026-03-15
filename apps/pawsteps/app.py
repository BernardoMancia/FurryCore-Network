import os
import secrets
import random
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Importações de DB (Adaptar caminhos para estrutura multi-app)
from database.db_social import SocialDatabaseManager
from models.social_user import SocialUser
# Para verificar a carteira (Selo Furry Verificado)
import sqlite3
from werkzeug.security import generate_password_hash
import sys

# Importar o core_i18n
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core_i18n import configure_i18n

load_dotenv()

app = Flask(__name__)
configure_i18n(app)
app.config['SECRET_KEY'] = os.getenv('SOCIAL_SECRET_KEY', 'paw-secret-789')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'events')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

csrf = CSRFProtect(app)
db = SocialDatabaseManager()
from werkzeug.utils import secure_filename


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_social'

@login_manager.user_loader
def load_user(user_id):
    return SocialUser.get(user_id)

# Configuração de Segurança de Cabeçalhos (Middleware)
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Helper para verificar CGRF (Banco Externo)
def check_cgrf_verified(cnf):
    if not cnf: return False
    # Caminho correto: um nível acima para 'apps', depois para 'cgrf/base_cgrf.db'
    cgrf_db_path = os.path.join(os.path.dirname(__file__), '../cgrf/base_cgrf.db')
    try:
        conn = sqlite3.connect(cgrf_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT is_valido FROM cidadaos WHERE cnf = ?", (cnf,))
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else False
    except:
        return False

@app.route('/')
def index():
    """Timeline Pública (Apenas SFW)"""
    # Consulta avançada com contagem de likes, reposts, comments e estado do current_user
    uid = current_user.id if current_user.is_authenticated else -1
    
    query = f"""
    SELECT p.*, 
           u.username, u.display_name, u.avatar_url, u.cnf_vinculado,
           (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) as likes_count,
           (SELECT COUNT(*) FROM post_reposts WHERE post_id = p.id) as reposts_count,
           (SELECT COUNT(*) FROM posts WHERE reply_to_post_id = p.id) as replies_count,
           (SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = {uid}) as user_liked,
           (SELECT 1 FROM post_saves WHERE post_id = p.id AND user_id = {uid}) as user_saved,
           (SELECT 1 FROM post_reposts WHERE post_id = p.id AND user_id = {uid}) as user_reposted,
           orig_u.username as orig_username, orig_u.display_name as orig_display_name, orig_u.avatar_url as orig_avatar_url,
           orig_p.content as orig_content, orig_p.media_url as orig_media_url
    FROM posts p
    JOIN users u ON p.user_id = u.id
    LEFT JOIN posts orig_p ON p.original_post_id = orig_p.id
    LEFT JOIN users orig_u ON orig_p.user_id = orig_u.id
    WHERE p.is_nsfw = 0 AND p.reply_to_post_id IS NULL
    ORDER BY p.created_at DESC
    LIMIT 50
    """
    posts = db.execute_query(query, fetchall=True)
    
    # Adicionar flag de verificado
    posts_list = []
    for p in posts:
        p_dict = dict(p)
        cnf_check = p_dict.get('cnf_vinculado')
        # Se for repost, a CNF verificada deve vir do dono original se exibirmos, 
        # mas checando a do post mesmo:
        p_dict['is_verified'] = check_cgrf_verified(cnf_check)
        posts_list.append(p_dict)
        
    return render_template('index.html', posts=posts_list)

@app.route('/login', methods=['GET', 'POST'])
def login_social():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = SocialUser.find_by_username(username)
        if user and user.check_password(password):
            if user.status == 'PENDENTE':
                flash("Sua conta ainda não foi ativada. Por favor, ative-a no portal CGRF.", "warning")
            elif user.status != 'ATIVO':
                flash("Sua conta está desativada ou suspensa.", "error")
            else:
                login_user(user)
                return redirect(url_for('index'))
        else:
            flash("Usuário ou senha inválidos.", "error")
    return render_template('login_social.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').replace(' ', '')
        display_name = request.form.get('display_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("As senhas não coincidem.", "error")
            return render_template('register.html')
            
        # CNF é opcional no banco, mas removido do form público para restrição
        is_plus18 = 1 if request.form.get('is_plus18') else 0
        age = request.form.get('age')
        
        if not username:
            flash("Username inválido.", "error")
            return render_template('register.html')

        pwd_hash = generate_password_hash(password)
        
        colors = ['b6e3f4', 'c0aede', 'd1d4f9', 'ffd5dc', 'ffdfbf', 'ff9a9e', 'fecfef']
        bg_color = random.choice(colors)
        avatar_url = f"https://api.dicebear.com/7.x/big-ears/svg?seed={username}&backgroundColor={bg_color}"
        
        try:
            db.execute_query(
                "INSERT INTO users (username, display_name, email, password_hash, is_plus18, avatar_url, status) VALUES (?, ?, ?, ?, ?, ?, 'ATIVO')",
                (username, display_name, email, pwd_hash, is_plus18, avatar_url)
            )
            flash("Cadastro realizado! Faça login.", "success")
            return redirect(url_for('login_social'))
        except Exception as e:
            flash("Erro ao cadastrar. Username ou e-mail já existem.", "error")
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout_social():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')
    is_nsfw = 1 if request.form.get('is_nsfw') else 0
    event_id = request.form.get('event_id')
    location = request.form.get('location')
    reply_to = request.form.get('reply_to_post_id')
    
    if content:
        db.execute_query(
            "INSERT INTO posts (user_id, content, is_nsfw, event_id, location, reply_to_post_id) VALUES (?, ?, ?, ?, ?, ?)",
            (current_user.id, content, is_nsfw, event_id, location, reply_to)
        )
        flash("Postado com sucesso!", "success")
    # Redireciona de volta para onde estava (index ou details)
    return redirect(request.referrer or url_for('index'))

@app.route('/api/toggle_like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like(post_id):
    existing = db.execute_query("SELECT 1 FROM post_likes WHERE user_id = ? AND post_id = ?", (current_user.id, post_id), fetchone=True)
    if existing:
        db.execute_query("DELETE FROM post_likes WHERE user_id = ? AND post_id = ?", (current_user.id, post_id))
        liked = False
    else:
        db.execute_query("INSERT INTO post_likes (user_id, post_id) VALUES (?, ?)", (current_user.id, post_id))
        liked = True
    
    count = db.execute_query("SELECT COUNT(*) as c FROM post_likes WHERE post_id = ?", (post_id,), fetchone=True)['c']
    return jsonify({"liked": liked, "count": count})

@app.route('/api/toggle_save/<int:post_id>', methods=['POST'])
@login_required
def toggle_save(post_id):
    existing = db.execute_query("SELECT 1 FROM post_saves WHERE user_id = ? AND post_id = ?", (current_user.id, post_id), fetchone=True)
    if existing:
        db.execute_query("DELETE FROM post_saves WHERE user_id = ? AND post_id = ?", (current_user.id, post_id))
        saved = False
    else:
        db.execute_query("INSERT INTO post_saves (user_id, post_id) VALUES (?, ?)", (current_user.id, post_id))
        saved = True
    return jsonify({"saved": saved})

@app.route('/api/toggle_repost/<int:post_id>', methods=['POST'])
@login_required
def toggle_repost(post_id):
    existing = db.execute_query("SELECT 1 FROM post_reposts WHERE user_id = ? AND post_id = ?", (current_user.id, post_id), fetchone=True)
    if existing:
        db.execute_query("DELETE FROM post_reposts WHERE user_id = ? AND post_id = ?", (current_user.id, post_id))
        # Remover o post espelhado
        db.execute_query("DELETE FROM posts WHERE original_post_id = ? AND user_id = ?", (post_id, current_user.id))
        reposted = False
    else:
        db.execute_query("INSERT INTO post_reposts (user_id, post_id) VALUES (?, ?)", (current_user.id, post_id))
        # Criar post espelho
        db.execute_query("INSERT INTO posts (user_id, is_repost, original_post_id) VALUES (?, 1, ?)", (current_user.id, post_id))
        reposted = True
        
    count = db.execute_query("SELECT COUNT(*) as c FROM post_reposts WHERE post_id = ?", (post_id,), fetchone=True)['c']
    return jsonify({"reposted": reposted, "count": count})

@app.route('/explore')
def explore():
    import re
    from collections import Counter
    
    recent_posts = db.execute_query("SELECT content FROM posts ORDER BY created_at DESC LIMIT 200", fetchall=True)
    hashtags = []
    for p in recent_posts:
        if p['content']:
            tags = re.findall(r'#\w+', p['content'])
            hashtags.extend(tags)
            
    trends = Counter(hashtags).most_common(10)
    
    if current_user.is_authenticated:
        suggestions = db.execute_query(f"""
            SELECT * FROM users 
            WHERE status = 'ATIVO' AND id != {current_user.id} 
            AND id NOT IN (SELECT followed_id FROM follows WHERE follower_id = {current_user.id})
            ORDER BY RANDOM() LIMIT 5
        """, fetchall=True)
    else:
        suggestions = db.execute_query("SELECT * FROM users WHERE status = 'ATIVO' ORDER BY RANDOM() LIMIT 5", fetchall=True)
        
    return render_template('explore.html', trends=trends, suggestions=suggestions)

@app.route('/api/toggle_follow/<username>', methods=['POST'])
@login_required
def toggle_follow(username):
    target = db.execute_query("SELECT id FROM users WHERE username = ?", (username,), fetchone=True)
    if not target: return jsonify({"error": "Usuário não encontrado"}), 404
    
    existing = db.execute_query("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (current_user.id, target['id']), fetchone=True)
    if existing:
        db.execute_query("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (current_user.id, target['id']))
        following = False
    else:
        db.execute_query("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", (current_user.id, target['id']))
        following = True
        
    return jsonify({"following": following})

@app.route('/messages')
@login_required
def messages_index():
    chats = db.execute_query("""
        SELECT DISTINCT u.username, u.display_name, u.avatar_url
        FROM messages m
        JOIN users u ON (m.sender_id = u.id OR m.receiver_id = u.id)
        WHERE (m.sender_id = ? OR m.receiver_id = ?) AND u.id != ?
    """, (current_user.id, current_user.id, current_user.id), fetchall=True)
    return render_template('messages.html', chats=chats, active_chat=None)

@app.route('/messages/<username>', methods=['GET', 'POST'])
@login_required
def chat(username):
    other_user = db.execute_query("SELECT * FROM users WHERE username = ?", (username,), fetchone=True)
    if not other_user:
        flash("Usuário inexistente.", "error")
        return redirect(url_for('messages_index'))
        
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            db.execute_query(
                "INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                (current_user.id, other_user['id'], content)
            )
        return redirect(url_for('chat', username=username))
        
    msgs = db.execute_query("""
        SELECT * FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
    """, (current_user.id, other_user['id'], other_user['id'], current_user.id), fetchall=True)
    
    chats = db.execute_query("""
        SELECT DISTINCT u.username, u.display_name, u.avatar_url
        FROM messages m
        JOIN users u ON (m.sender_id = u.id OR m.receiver_id = u.id)
        WHERE (m.sender_id = ? OR m.receiver_id = ?) AND u.id != ?
    """, (current_user.id, current_user.id, current_user.id), fetchall=True)
    
    return render_template('messages.html', chats=chats, active_chat=other_user, messages=msgs)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        bio = request.form.get('bio')
        avatar_url = request.form.get('avatar_url')
        profile_cover_url = request.form.get('profile_cover_url')
        mfa_enabled = 1 if request.form.get('mfa_enabled') else 0
        view_nsfw = 1 if request.form.get('view_nsfw') else 0
        share_location = 1 if request.form.get('share_location') else 0
        
        # Lógica de Upload de Avatar e Capa
        avatar_file = request.files.get('avatar_file')
        cover_file = request.files.get('cover_file')
        
        if avatar_file and avatar_file.filename != '':
            filename = secure_filename(f"avatar_{current_user.id}_{secrets.token_hex(4)}_{avatar_file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(filepath)
            avatar_url = f"/static/uploads/{filename}"
            
        if cover_file and cover_file.filename != '':
            filename = secure_filename(f"cover_{current_user.id}_{secrets.token_hex(4)}_{cover_file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover_file.save(filepath)
            profile_cover_url = f"/static/uploads/{filename}"

        try:
            db.execute_query(
                "UPDATE users SET display_name=?, email=?, phone_number=?, bio=?, avatar_url=?, profile_cover_url=?, mfa_enabled=?, view_nsfw=?, share_location=? WHERE id=?",
                (display_name, email, phone_number, bio, avatar_url, profile_cover_url, mfa_enabled, view_nsfw, share_location, current_user.id)
            )
            flash("Perfil atualizado com sucesso!", "success")
            return redirect(url_for('profile', username=current_user.username))
        except Exception as e:
            flash("Erro ao salvar perfil.", "error")
            
        return redirect(url_for('edit_profile'))
        
    user_data = db.execute_query("SELECT * FROM users WHERE id = ?", (current_user.id,), fetchone=True)
    return render_template('edit_profile.html', user=user_data)

@app.route('/settings')
def settings_redirect():
    return redirect(url_for('edit_profile'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = db.execute_query("SELECT * FROM users WHERE username = ?", (username,), fetchone=True)
    if not user:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('index'))
        
    is_owner = (current_user.id == user['id'])
    
    # Contagens
    followers = db.execute_query("SELECT COUNT(*) as c FROM follows WHERE followed_id = ?", (user['id'],), fetchone=True)['c']
    following = db.execute_query("SELECT COUNT(*) as c FROM follows WHERE follower_id = ?", (user['id'],), fetchone=True)['c']
    
    # Aba atual
    tab = request.args.get('tab', 'posts')
    
    # Query base para renderizar posts compatíveis com o formato do feed
    uid = current_user.id
    base_post_query_select = f"""
    SELECT p.*, 
           u.username, u.display_name, u.avatar_url, u.cnf_vinculado,
           (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) as likes_count,
           (SELECT COUNT(*) FROM post_reposts WHERE post_id = p.id) as reposts_count,
           (SELECT COUNT(*) FROM posts WHERE reply_to_post_id = p.id) as replies_count,
           (SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = {uid}) as user_liked,
           (SELECT 1 FROM post_saves WHERE post_id = p.id AND user_id = {uid}) as user_saved,
           (SELECT 1 FROM post_reposts WHERE post_id = p.id AND user_id = {uid}) as user_reposted,
           orig_u.username as orig_username, orig_u.display_name as orig_display_name, orig_u.avatar_url as orig_avatar_url,
           orig_p.content as orig_content, orig_p.media_url as orig_media_url
    """
    base_post_query_from = """
    FROM posts p
    JOIN users u ON p.user_id = u.id
    LEFT JOIN posts orig_p ON p.original_post_id = orig_p.id
    LEFT JOIN users orig_u ON orig_p.user_id = orig_u.id
    """
    
    if tab == 'posts':
        query = base_post_query_select + base_post_query_from + f" WHERE p.user_id = {user['id']} AND p.reply_to_post_id IS NULL ORDER BY p.created_at DESC"
    elif tab == 'replies':
        query = base_post_query_select + base_post_query_from + f" WHERE p.user_id = {user['id']} AND p.reply_to_post_id IS NOT NULL ORDER BY p.created_at DESC"
    elif tab == 'media':
        query = base_post_query_select + base_post_query_from + f" WHERE p.user_id = {user['id']} AND p.media_url IS NOT NULL ORDER BY p.created_at DESC"
    elif tab == 'likes' and is_owner:
        query = base_post_query_select + base_post_query_from + f" JOIN post_likes pl ON p.id = pl.post_id WHERE pl.user_id = {user['id']} ORDER BY pl.created_at DESC"
    elif tab == 'saves' and is_owner:
        query = base_post_query_select + base_post_query_from + f" JOIN post_saves ps ON p.id = ps.post_id WHERE ps.user_id = {user['id']} ORDER BY ps.created_at DESC"
    else:
        query = base_post_query_select + base_post_query_from + f" WHERE p.user_id = {user['id']} AND p.reply_to_post_id IS NULL ORDER BY p.created_at DESC"
        
    posts_raw = db.execute_query(query, fetchall=True)
    posts_list = [dict(p) for p in posts_raw]
    
    return render_template('profile.html', user_profile=user, posts=posts_list, tab=tab, is_owner=is_owner, followers=followers, following=following)

@app.route('/events')
def events():
    """Lista de Eventos com Drill-down"""
    import json
    name_filter = request.args.get('name')
    year_filter = request.args.get('year')
    category_filter = request.args.get('category')
    
    query = "SELECT * FROM events WHERE is_approved = 1"
    params = []
    
    if name_filter:
        query += " AND name = ?"
        params.append(name_filter)
    if year_filter:
        query += " AND year = ?"
        params.append(year_filter)
    if category_filter:
        query += " AND (city = ? OR country = ?)" # Exemplo de categoria por local
        params.append(category_filter)
        params.append(category_filter)

    # Se não logado ou não +18, nunca mostra NSFW fixo
    if not current_user.is_authenticated or not getattr(current_user, 'is_plus18', 0):
        query += " AND is_nsfw = 0"
        
    events_raw = db.execute_query(query, params, fetchall=True)
    
    # Aqui a lógica do drill-down mudou: o index agora apenas lista as capas dos eventos
    categories = ["Brasil", "EUA", "Europa", "Online"]
    events_list = []
    
    seen_names = set()
    for e in events_raw:
        ed = dict(e)
        if ed['name'] not in seen_names:
            events_list.append(ed)
            seen_names.add(ed['name'])
        
    return render_template('events.html', events=events_list, categories=categories)

@app.route('/event/<slug>')
def event_details(slug):
    # Puxar todos os anos/edições válidos deste evento usando SLUG
    event_base = db.execute_query("SELECT name FROM events WHERE slug = ? OR name = ? LIMIT 1", (slug, slug.replace('-', ' ')), fetchone=True)
    if not event_base:
        flash("Evento não encontrado.", "error")
        return redirect(url_for('events'))
    
    name = event_base['name']
    event_records = db.execute_query("SELECT id, year FROM events WHERE name = ? AND is_approved = 1 ORDER BY year DESC", (name,), fetchall=True)
        
    event_ids = [str(r['id']) for r in event_records]
    years_available_for_upload = [{'id': r['id'], 'year': r['year']} for r in event_records]
    
    # Buscar anos que de fato possuem mídias para exibição nas abas
    posts_query = f"""
        SELECT p.*, e.year, u.username, u.display_name, u.avatar_url 
        FROM posts p
        JOIN events e ON p.event_id = e.id
        JOIN users u ON p.user_id = u.id
        WHERE p.event_id IN ({','.join(event_ids)})
        AND p.media_url IS NOT NULL
    """
    
    # Conferir se o usuário pode ver conteúdo NSFW
    view_nsfw_pref = 0
    if current_user.is_authenticated:
        u_pref = db.execute_query("SELECT view_nsfw FROM users WHERE id=?", (current_user.id,), fetchone=True)
        view_nsfw_pref = u_pref['view_nsfw'] if u_pref else 0

    if not current_user.is_authenticated or not getattr(current_user, 'is_plus18', 0) or not view_nsfw_pref:
        posts_query += " AND p.is_nsfw = 0"
        
    posts_query += " ORDER BY p.created_at DESC"
    posts = db.execute_query(posts_query, fetchall=True)
    
    years_with_media = sorted(list(set([p['year'] for p in posts])), reverse=True)
    current_year = request.args.get('year', str(years_with_media[0]) if years_with_media else "")
    
    return render_template('event_details.html', 
                          event_name=name, 
                          slug=slug,
                          posts=[dict(p) for p in posts], 
                          years_with_media=years_with_media,
                          years_available_for_upload=years_available_for_upload,
                          current_year=current_year)

@app.route('/post_event_media/<slug>', methods=['POST'])
@login_required
def post_event_media(slug):
    import base64
    event_id = request.form.get('event_id')
    manual_year = request.form.get('manual_year')
    title = request.form.get('title')
    content = request.form.get('content')
    is_nsfw = 1 if request.form.get('is_nsfw') else 0
    file = request.files.get('media_file')
    cropped_b64 = request.form.get('cropped_image_base64')
    
    if not event_id and not manual_year:
        flash("Selecione ou digite um ano para enviar.", "error")
        return redirect(url_for('event_details', slug=slug))
        
    if not event_id and manual_year:
        try:
            year_int = int(manual_year)
            base_event = db.execute_query("SELECT * FROM events WHERE slug = ? OR name = ? LIMIT 1", (slug, slug.replace('-', ' ')), fetchone=True)
            if base_event:
                name = base_event['name']
                existing = db.execute_query("SELECT id FROM events WHERE name = ? AND year = ?", (name, year_int), fetchone=True)
                if existing:
                    event_id = existing['id']
                else:
                    event_id = db.execute_query(
                        "INSERT INTO events (creator_id, name, slug, description, location_address, city, country, social_link, year, is_approved) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                        (current_user.id, name, slug, base_event['description'], base_event['location_address'], base_event['city'], base_event['country'], base_event['social_link'], year_int)
                    )
            else:
                flash("Evento indisponível.", "error")
                return redirect(url_for('events'))
        except ValueError:
            flash("Ano deve ser numérico.", "error")
            return redirect(url_for('event_details', slug=slug))

    if not cropped_b64 and (not file or file.filename == ''):
        flash("Nenhuma mídia detectada para enviar.", "error")
        return redirect(url_for('event_details', name=name))

    filepath = ""
    filename = ""

    # Se recebeu um Base64 do Cropper.js (Imagem Editada)
    if cropped_b64:
        try:
            # Separar o header "data:image/jpeg;base64," do payload
            header, encoded = cropped_b64.split(",", 1)
            ext = 'jpg'
            if 'png' in header: ext = 'png'
            filename = secure_filename(f"{secrets.token_hex(8)}_cropped.{ext}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            with open(filepath, "wb") as fh:
                fh.write(base64.b64decode(encoded))
        except Exception as e:
            flash("Erro ao processar imagem editada.", "error")
            return redirect(url_for('event_details', name=name))

    # Se não há Base64, é possivelmente um vídeo upado do file normal
    else:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            flash("Formato de arquivo não suportado.", "error")
            return redirect(url_for('event_details', name=name))
            
        filename = secure_filename(f"{secrets.token_hex(8)}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    media_url = f"/static/uploads/events/{filename}"
    
    db.execute_query(
        "INSERT INTO posts (user_id, title, content, is_nsfw, event_id, media_url) VALUES (?, ?, ?, ?, ?, ?)",
        (current_user.id, title, content, is_nsfw, event_id, media_url)
    )
    
    flash("Sua mídia foi salva com sucesso no álbum do evento!", "success")
    return redirect(url_for('event_details', name=name))


@app.route('/vincular', methods=['GET', 'POST'])
def vincular_cnf():
    """
    Permite vincular uma CNF recebida por e-mail a uma conta existente.
    Acessível apenas via link no e-mail de emissão.
    """
    cnf = request.args.get('cnf')
    email_emissao = request.args.get('email')
    
    if not cnf or not email_emissao:
        flash("Link de vinculação inválido ou incompleto.", "error")
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = SocialUser.find_by_username(username)
        if user and user.check_password(password):
            # Vincular CNF à conta encontrada
            db.execute_query("UPDATE users SET cnf_vinculado = ? WHERE id = ?", (cnf, user.id))
            
            # Se havia uma conta pré-criada para esse e-mail (que não é a atual), podemos desativá-la
            if user.email != email_emissao:
                db.execute_query("UPDATE users SET status = 'INATIVO' WHERE email = ? AND id != ?", (email_emissao, user.id))
            
            login_user(user)
            flash(f"Sua CNF {cnf} foi vinculada com sucesso à sua conta {username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Credenciais inválidas para vinculação.", "error")
            
    return render_template('vincular_cnf.html', cnf=cnf, email=email_emissao)

# --- SISTEMA DE MAPA E LOCALIZAÇÃO (SEGURANÇA FURRY) ---

def apply_noise(coord):
    """Aplica ruído aleatório de ~100m para segurança."""
    # 1 grau de latitude ~ 111.32 km
    # 100m ~ 0.000898 graus
    noise = (random.uniform(-1, 1)) * 0.000898
    return coord + noise

@app.route('/api/update-location', methods=['POST'])
@login_required
def update_location():
    """Atualiza localização com ofuscação."""
    data = request.json
    lat = float(data.get('lat'))
    lng = float(data.get('lng'))
    active = data.get('active', False)
    
    # Aplicar erro de 100m de propósito
    noise_lat = apply_noise(lat)
    noise_lng = apply_noise(lng)
    
    db.execute_query(
        "INSERT OR REPLACE INTO location_pins (user_id, lat, lng, is_active, last_updated) VALUES (?, ?, ?, ?, ?)",
        (current_user.id, noise_lat, noise_lng, active, datetime.now())
    )
    return jsonify({"status": "success", "message": "Localização atualizada com ruído de segurança."})

@app.route('/api/nearby-users')
def get_nearby_users():
    """Retorna usuários próximos (pins ofuscados) filtrando por quem permite compartilhamento."""
    users = db.execute_query("""
        SELECT u.username, u.display_name, l.lat, l.lng 
        FROM location_pins l 
        JOIN users u ON l.user_id = u.id 
        WHERE l.is_active = 1 AND u.share_location = 1
    """, fetchall=True)
    return jsonify([dict(u) for u in users])

@app.route('/map')
def map_view():
    """Página do Mapa de Proximidade."""
    return render_template('map.html')

@app.route('/lang/<lang>')
def set_language(lang):
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=20001, debug=True)
