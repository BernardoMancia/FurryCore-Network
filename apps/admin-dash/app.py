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
    'cgrf': '/app/shared_data/cgrf/base_cgrf.db',
    'pawsteps': '/app/shared_data/pawsteps/pawsteps.db',
    'shop': '/app/shared_data/shop/shop.db'
}
LOG_PATH = '/app/shared_logs/access.log'

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=29999, debug=True)
