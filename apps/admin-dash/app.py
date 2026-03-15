import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('ADMIN_SECRET_KEY', 'cyber-furry-admin-9999')

# Configurações de Caminhos (Mapeados via Docker Volumes)
DB_PATHS = {
    'cgrf': '/app/shared_data/cgrf/database/base_cgrf.db',
    'pawsteps': '/app/shared_data/pawsteps/pawsteps.db',
    'shop': '/app/shared_data/shop/shop.db'
}
LOG_PATH = '/app/shared_logs/access_log.log'

# Banco de Dados do Próprio Dashboard
ADMIN_DB_PATH = 'database/admin_panel.db'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class AdminUser(UserMixin):
    def __init__(self, id, username, must_change):
        self.id = id
        self.username = username
        self.must_change = must_change

def get_admin_db():
    conn = sqlite3.connect(ADMIN_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_admin_db():
    if not os.path.exists('database'):
        os.makedirs('database')
    conn = get_admin_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        must_change_password BOOLEAN DEFAULT 1
    )''')
    # Cria o usuário inicial se não existir
    user = conn.execute('SELECT * FROM admin_users WHERE username = ?', ('Luke_Arwolf',)).fetchone()
    if not user:
        hashed = generate_password_hash('senha123')
        conn.execute('INSERT INTO admin_users (username, password, must_change_password) VALUES (?, ?, 1)', 
                     ('Luke_Arwolf', hashed))
    conn.commit()
    conn.close()

init_admin_db()

@login_manager.user_loader
def load_user(user_id):
    conn = get_admin_db()
    user = conn.execute('SELECT * FROM admin_users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return AdminUser(user['id'], user['username'], user['must_change_password'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_admin_db()
        user = conn.execute('SELECT * FROM admin_users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            admin_user = AdminUser(user['id'], user['username'], user['must_change_password'])
            login_user(admin_user)
            if admin_user.must_change:
                return redirect(url_for('change_password'))
            return redirect(url_for('index'))
        flash('Credenciais inválidas.', 'danger')
    return render_template('login.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        hashed = generate_password_hash(new_password)
        conn = get_admin_db()
        conn.execute('UPDATE admin_users SET password = ?, must_change_password = 0 WHERE id = ?', 
                     (hashed, current_user.id))
        conn.commit()
        conn.close()
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('change_password.html')

@app.route('/')
@login_required
def index():
    if current_user.must_change:
        return redirect(url_for('change_password'))
    return render_template('index.html')

# --- Monitoramento ---
@app.route('/api/stats')
@login_required
def get_stats():
    # Análise básica de logs do Nginx
    stats = {
        'total_requests': 0,
        'status_200': 0,
        'status_404': 0,
        'status_500': 0,
        'recent_ips': [],
        'security_alerts': []
    }
    
    if os.path.exists(LOG_PATH):
        try:
            # Lógica simplificada de parsing de log
            with open(LOG_PATH, 'r') as f:
                lines = f.readlines()[-500:] # Últimas 500 requisições
                stats['total_requests'] = len(lines)
                for line in lines:
                    if ' 200 ' in line: stats['status_200'] += 1
                    elif ' 404 ' in line: stats['status_404'] += 1
                    elif ' 500 ' in line or ' 502 ' in line: stats['status_500'] += 1
                    
                    # Alerta Simples de Segurança (ex: tentando acessar .env)
                    if '.env' in line or 'wp-admin' in line or 'config' in line:
                        stats['security_alerts'].append(f"Tentativa suspeita detectada: {line[:50]}...")
        except:
            pass
            
    return jsonify(stats)

# --- Gestão de Banco de Dados ---
@app.route('/database/<app_name>')
@login_required
def view_db(app_name):
    if app_name not in DB_PATHS:
        return "App não encontrado", 404
    
    db_path = DB_PATHS[app_name]
    if not os.path.exists(db_path):
        return f"Banco de dados de {app_name} não encontrado no path mapeado.", 404
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()
    
    return render_template('view_db.html', app_name=app_name, tables=tables)

@app.route('/database/<app_name>/<table>')
@login_required
def view_table(app_name, table):
    db_path = DB_PATHS[app_name]
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    data = conn.execute(f"SELECT * FROM {table} LIMIT 100").fetchall()
    columns = data[0].keys() if data else []
    conn.close()
    return render_template('view_table.html', app_name=app_name, table=table, columns=columns, data=data)

# --- Segurança e Logs de Invasão ---
@app.route('/security')
@login_required
def view_security():
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r') as f:
            lines = f.readlines()[-100:] # Últimos 100 logs
            for line in lines:
                if any(x in line for x in ['.env', 'wp-admin', 'config', 'phpinfo', '403', '404']):
                    logs.append(line)
    return render_template('security.html', logs=logs)

# --- Gestão Global de Admins ---
@app.route('/admins')
@login_required
def manage_admins():
    conn = get_admin_db()
    dash_admins = conn.execute("SELECT * FROM admin_users").fetchall()
    conn.close()
    
    # Tentativa de ler admins das outras apps (SQLite)
    app_admins = {}
    for app_name, path in DB_PATHS.items():
        if os.path.exists(path):
            try:
                conn_app = sqlite3.connect(path)
                conn_app.row_factory = sqlite3.Row
                # Verifica se a tabela users existe e tem is_admin
                tables = [t[0] for t in conn_app.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                if 'users' in tables:
                     app_admins[app_name] = conn_app.execute("SELECT * FROM users WHERE is_admin = 1").fetchall()
                conn_app.close()
            except:
                app_admins[app_name] = []
                
    return render_template('admins.html', dash_admins=dash_admins, app_admins=app_admins)

@app.route('/admins/add', methods=['POST'])
@login_required
def add_admin():
    username = request.form.get('username')
    password = generate_password_hash(request.form.get('password'))
    conn = get_admin_db()
    try:
        conn.execute("INSERT INTO admin_users (username, password, must_change_password) VALUES (?, ?, ?)", (username, password, 0))
        conn.commit()
        flash(f"Admin {username} criado com sucesso.", "success")
    except:
        flash("Erro ao criar admin (usuário já existe?)", "danger")
    conn.close()
    return redirect(url_for('manage_admins'))

@app.route('/admins/delete/<int:admin_id>')
@login_required
def delete_admin(admin_id):
    if admin_id == current_user.id:
        flash("Você não pode deletar a si mesmo!", "danger")
        return redirect(url_for('manage_admins'))
    conn = get_admin_db()
    conn.execute("DELETE FROM admin_users WHERE id = ?", (admin_id,))
    conn.commit()
    conn.close()
    flash("Admin removido.", "info")
    return redirect(url_for('manage_admins'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- GESTÃO CGRF (CONSOLIDADA) ---

@app.route('/cgrf/users', methods=['GET', 'POST'])
@login_required
def cgrf_manage_users():
    db_path = DB_PATHS['cgrf']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = generate_password_hash(request.form.get('password'))
        cargo = request.form.get('cargo')
        cnf = request.form.get('cnf')
        try:
            conn.execute("INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado) VALUES (?, ?, ?, ?)", (email, password, cargo, cnf or None))
            conn.commit()
            flash(f"Usuário {email} criado no CGRF.", "success")
        except Exception as e:
            flash(f"Erro ao criar usuário: {e}", "danger")
            
    usuarios = conn.execute("SELECT * FROM usuarios_sistema").fetchall()
    conn.close()
    return render_template('cgrf_users.html', usuarios=usuarios)

@app.route('/cgrf/emit', methods=['GET', 'POST'])
@login_required
def cgrf_emit_wallet():
    if request.method == 'POST':
        nome = request.form.get('nome')
        especie = request.form.get('especie')
        regiao = request.form.get('regiao')
        cidade = request.form.get('cidade')
        idiomas_list = request.form.getlist('idiomas')
        idiomas = ", ".join(idiomas_list) if idiomas_list else "Não Informado"
        email = request.form.get('email')
        foto_base64_raw = request.form.get('foto_base64')
        
        cnf = gerar_cnf()
        rgf = gerar_rgf()
        qr_base64 = gerar_qrcode_base64(cnf)
        
        foto_base64 = None
        if foto_base64_raw and "," in foto_base64_raw:
            foto_base64 = foto_base64_raw.split(",")[1]
            
        hoje = datetime.now()
        exp = hoje.replace(year=hoje.year + 10)
        
        db_path = DB_PATHS['cgrf']
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("""INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, cidade, idiomas, email, data_emissao, data_expiracao, qrcode_base64, foto_base64)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                           (cnf, rgf, nome, especie, regiao, cidade, idiomas, email, hoje.strftime("%d/%m/%Y"), exp.strftime("%d/%m/%Y"), qr_base64, foto_base64))
            
            # Criar conta automática
            if email:
                temp_pass = secrets.token_urlsafe(12)
                pwd_hash = generate_password_hash(temp_pass)
                conn.execute("INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado, status) VALUES (?, ?, ?, ?, ?)",
                             (email, pwd_hash, 'USUARIO', cnf, 'PENDENTE'))
                
                # Mock do welcome email (requer app context se for usar current_app)
                user_data = {'nome': nome, 'cnf': cnf, 'rgf': rgf, 'email': email, 'temp_pass': temp_pass}
                send_welcome_email(user_data)
                
            conn.commit()
            flash(f"Carteira de {nome} emitida com sucesso! CNF: {cnf}", "success")
        except Exception as e:
            flash(f"Erro na emissão: {e}", "danger")
        finally:
            conn.close()
        return redirect(url_for('cgrf_manage_records'))
        
    return render_template('cgrf_emitir.html')

@app.route('/cgrf/records')
@login_required
def cgrf_manage_records():
    db_path = DB_PATHS['cgrf']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    registros = conn.execute("SELECT * FROM cidadaos WHERE is_valido = 1 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('cgrf_registros.html', registros=registros)

@app.route('/cgrf/privacy')
@login_required
def cgrf_manage_privacy():
    db_path = DB_PATHS['cgrf']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
    SELECT s.*, c.nome as nome_cidadao 
    FROM solicitacoes_privacidade s
    JOIN cidadaos c ON s.cnf_solicitante = c.cnf
    WHERE s.status = 'PENDENTE'
    ORDER BY s.data_solicitacao ASC
    """
    solicitacoes = conn.execute(query).fetchall()
    conn.close()
    return render_template('cgrf_privacidade.html', solicitacoes=solicitacoes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=29999, debug=True)
