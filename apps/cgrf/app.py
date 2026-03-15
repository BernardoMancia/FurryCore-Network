import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from database.db_manager import DatabaseManager
from models.user import User
from utils.security import sanitizar_input, formatar_data_sp
from utils.logic import gerar_cnf, gerar_rgf, gerar_qrcode_base64
from utils.auth_utils import role_required
from utils.mfa import validar_totp
from utils.email_utils import send_welcome_email

# Banco de Dados Social (PawSteps) para Integração
# Banco de Dados Social (PawSteps) para Integração em Docker
def get_social_db_path():
    # 1. Tentar caminho do container (Volume compartilhado)
    docker_path = '/app/shared_data/pawsteps/pawsteps.db'
    if os.path.exists(docker_path):
        return docker_path
    
    # 2. Tentar caminho relativo ao arquivo atual (Pasta superior)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fallback_path = os.path.join(base_dir, 'pawsteps', 'database', 'pawsteps.db')
    
    return fallback_path

def create_pre_account_social(email, display_name):
    """Cria uma conta pendente na rede social PawSteps"""
    try:
        import sqlite3
        from werkzeug.security import generate_password_hash
        db_path = get_social_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        username = email.split('@')[0].replace('.', '').replace('_', '').replace(' ', '')
        # Verificar se username existe
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            import random
            username += str(random.randint(100, 999))
            
        # Senha temporária padrão (será alterada na ativação)
        pwd_hash = generate_password_hash("PRE_CREATED_ACCOUNT_PW")
        
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, status) VALUES (?, ?, ?, ?, 'PENDENTE')",
            (username, display_name, email, pwd_hash)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Falha ao pre-criar conta social: {e}")
        return False

def sync_social_account(old_email, new_email, status=None, password_hash=None):
    """Sincroniza e-mail, status e senha com o banco Social"""
    try:
        import sqlite3
        db_path = get_social_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        if new_email:
            updates.append("email = ?")
            params.append(new_email)
        if status:
            updates.append("status = ?")
            params.append(status)
        if password_hash:
            updates.append("password_hash = ?")
            params.append(password_hash)
            
        if not updates: return False
        
        params.append(old_email)
        query = f"UPDATE users SET {', '.join(updates)} WHERE email = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Falha ao sincronizar conta social: {e}")
        return False

try:
    from core_i18n import configure_i18n
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core_i18n import configure_i18n

load_dotenv()

app = Flask(__name__)
configure_i18n(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Filtro para Jinja2 processar JSON
@app.template_filter('from_json')
def from_json_filter(s):
    import json
    try:
        return json.loads(s)
    except:
        return {}

csrf = CSRFProtect(app)
db = DatabaseManager()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.before_request
def monitor_session():
    """
    Monitoramento de sessão e sanitização global de inputs POST para prevenção de XSS.
    """
    session.permanent = True
    
    if request.method == 'POST':
        for key in request.form:
            request.form = request.form.copy()
            request.form[key] = sanitizar_input(request.form[key])

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Página inicial com motor de busca pública (CNF ou Nome).
    """
    if request.method == 'POST':
        query_val = request.form.get('cnf')
        if query_val:
            res = db.execute_query("SELECT cnf FROM cidadaos WHERE (cnf = ? OR nome LIKE ?) AND is_valido = 1", (query_val, f"%{query_val}%"), fetchone=True)
            if res:
                return redirect(url_for('perfil', cnf=res['cnf']))
            else:
                flash("Cidadão não encontrado na base de dados.", "error")
    return render_template('index.html')

@app.route('/test_emit')
def test_emit():
    cnf = gerar_cnf()
    rgf = gerar_rgf()
    qr = gerar_qrcode_base64(cnf)
    hoje = datetime.now()
    exp = hoje.replace(year=hoje.year + 10)
    
    data_emissao = formatar_data_sp(hoje)
    data_expiracao = formatar_data_sp(exp)
    
    query = """INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, qrcode_base64, foto_base64)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    # Exemplo de foto base64 (pixel transparente)
    foto_teste = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    params = (cnf, rgf, "Test User", "Fox", "South", "test@example.com", data_emissao, data_expiracao, qr, foto_teste)
    
    try:
        db.execute_query(query, params)
        return render_template('test_qr.html', cnf=cnf, qr=qr)
    except Exception as e:
        return f"Erro na emissão: {e}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Portal de acesso administrativo e pessoal.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.find_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            
            # Verificação de ativação (Fase 7)
            if user.status == 'PENDENTE':
                return redirect(url_for('ativar_conta'))
                
            if user.totp_secret:
                session['mfa_pending_user_id'] = user.id
                logout_user() # Força step do MFA
                return redirect(url_for('login_mfa'))
                
            return redirect(url_for('perfil', cnf=user.cnf_vinculado) if user.cargo == 'USUARIO' else url_for('index'))
        
        flash("Credenciais inválidas ou conta inexistente.", "error")
    
    return render_template('login.html')

@app.route('/login/mfa', methods=['GET', 'POST'])
def login_mfa():
    """
    Segundo fator de autenticação (MFA/TOTP).
    """
    user_id = session.get('mfa_pending_user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        token = request.form.get('token')
        user = User.get(user_id)
        
        if user and user.totp_secret and validar_totp(user.totp_secret, token):
            login_user(user)
            session.pop('mfa_pending_user_id', None)
            return redirect(url_for('index'))
        
        flash("Token MFA Inválido ou expirado.", "error")
        
    return render_template('login_mfa.html')

@app.route('/logout')
@login_required
def logout():
    """
    Encerramento de sessão.
    """
    logout_user()
    return redirect(url_for('login'))

@app.route('/perfil/<cnf>')
def perfil(cnf):
    import json
    """
    Visualização de perfil com motor de censura RBAC e LGPD.
    """
    cidadao = db.execute_query("SELECT * FROM cidadaos WHERE cnf = ? AND is_valido = 1", (cnf,), fetchone=True)
    if not cidadao:
        flash("Identidade digital não encontrada ou inativa.", "error")
        return redirect(url_for('index'))
    
    cidadao = dict(cidadao) # Converter para dict
    
    # RBAC: Titular vê tudo, visitante vê básico
    exibir_tudo = False
    if current_user.is_authenticated:
        if current_user.cargo in ['ADMIN', 'ANALISTA']:
            exibir_tudo = True
        elif current_user.cnf_vinculado == cnf:
            exibir_tudo = True
            
    # --- MOTOR DE CENSURA LGPD ---
    sob_revisao = []
    if cidadao.get('campos_sob_revisao'):
        try:
            sob_revisao = json.loads(cidadao['campos_sob_revisao'])
        except:
            sob_revisao = []
            
    # Se não for o titular, censura campos restritos e campos sob revisão
    if not exibir_tudo:
        for campo in sob_revisao:
            if campo in cidadao:
                cidadao[campo] = "[ DADO SOB REVISÃO (LGPD) ]"
            if campo == 'foto':
                cidadao['foto_base64'] = None
    
    return render_template('perfil.html', cidadao=cidadao, exibir_tudo=exibir_tudo, sob_revisao=sob_revisao)
@app.route('/create_admin')
def create_admin():
    from werkzeug.security import generate_password_hash
    # Rota temporária para criar um administrador inicial
    pwd = generate_password_hash("admin123")
    query = "INSERT INTO usuarios_sistema (email, senha_hash, cargo) VALUES (?, ?, ?)"
    try:
        db.execute_query(query, ("admin@cgrf.com", pwd, "ADMIN"))
        return "Admin criado com sucesso! E-mail: admin@cgrf.com | Senha: admin123"
    except Exception as e:
        return f"Erro ao criar admin: {e}"

@app.route('/admin/usuarios', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def admin_usuarios():
    return redirect("https://arwolf.com.br/cgrf/users")

@app.route('/admin/emitir', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def admin_emitir():
    return redirect("https://arwolf.com.br/cgrf/emit")

@app.route('/admin/registros')
@login_required
@role_required(['ADMIN', 'ANALISTA'])
def admin_registros():
    return redirect("https://arwolf.com.br/cgrf/records")

@app.route('/admin/privacidade')
@login_required
@role_required(['ADMIN'])
def admin_privacidade():
    return redirect("https://arwolf.com.br/cgrf/privacy")

@app.route('/admin/usuario/editar/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_usuario_editar(user_id):
    cargo = request.form.get('cargo')
    cnf = request.form.get('cnf')
    query = "UPDATE usuarios_sistema SET cargo = ?, cnf_vinculado = ? WHERE id = ?"
    db.execute_query(query, (cargo, cnf or None, user_id))
    flash("Configurações atualizadas.", "success")
    return redirect("https://arwolf.com.br/cgrf/users")

@app.route('/admin/usuario/excluir/<int:user_id>')
@login_required
@role_required(['ADMIN'])
def admin_usuario_excluir(user_id):
    db.execute_query("DELETE FROM usuarios_sistema WHERE id = ?", (user_id,))
    flash("Usuário removido.", "warning")
    return redirect("https://arwolf.com.br/cgrf/users")

@app.route('/admin/usuario/reenviar-email/<int:user_id>')
@login_required
@role_required(['ADMIN'])
def admin_usuario_reenviar_email_redir(user_id):
    return redirect(f"https://arwolf.com.br/cgrf/user/resend/{user_id}")

@app.route('/ativar-conta', methods=['GET', 'POST'])
@login_required
def ativar_conta():
    if current_user.status != 'PENDENTE':
        return redirect(url_for('index'))
    if request.method == 'POST':
        nova_senha = request.form.get('password')
        conf_senha = request.form.get('confirm_password')
        if nova_senha != conf_senha:
            flash("As senhas não coincidem.", "error")
            return render_template('ativar_conta.html')
        pwd_hash = generate_password_hash(nova_senha)
        db.execute_query("UPDATE usuarios_sistema SET senha_hash = ?, status = 'ATIVO' WHERE id = ?", (pwd_hash, current_user.id))
        sync_social_account(current_user.email, current_user.email, status='ATIVO', password_hash=pwd_hash)
        flash("Sua conta foi ativada com sucesso!", "success")
        return redirect(url_for('perfil', cnf=current_user.cnf_vinculado))
    return render_template('ativar_conta.html')

@app.route('/solicitar-privacidade', methods=['POST'])
@login_required
def solicitar_privacidade():
    import json
    cnf = current_user.cnf_vinculado
    if not cnf:
        flash("Sua conta não possui uma CNF vinculada para gerenciar privacidade.", "error")
        return redirect(url_for('index'))
        
    # Coleta de dados do formulário
    acoes = {}
    sob_revisao = []
    
    campos = ['nome', 'especie', 'regiao', 'foto']
    for campo in campos:
        action = request.form.get(f'action_{campo}', 'none')
        if action != 'none':
            acoes[campo] = {
                'acao': action,
                'novo_valor': request.form.get(f'value_{campo}')
            }
            sob_revisao.append(campo)
            
    # Caso de exclusão total
    if request.form.get('delete_all') == '1':
        acoes['delete_all'] = True
        
    if not acoes:
        flash("Nenhuma alteração solicitada.", "warning")
        return redirect(url_for('perfil', cnf=cnf))
        
    try:
        # 1. Registrar a solicitação no banco
        query_ticket = """INSERT INTO solicitacoes_privacidade (cnf_solicitante, tipo_acao, detalhes_json, data_solicitacao)
                          VALUES (?, ?, ?, ?)"""
        db.execute_query(query_ticket, (cnf, 'REMOVER' if 'delete_all' in acoes else 'ALTERAR', json.dumps(acoes), datetime.now().strftime("%d/%m/%Y %H:%M")))
        
        # 2. Atualizar campos sob revisão no cidadão para ocultação imediata
        # Buscamos os atuais para não sobrescrever se já existir algo
        curr_reg = db.execute_query("SELECT campos_sob_revisao FROM cidadaos WHERE cnf = ?", (cnf,), fetchone=True)
        already_revising = []
        if curr_reg and curr_reg['campos_sob_revisao']:
            try: already_revising = json.loads(curr_reg['campos_sob_revisao'])
            except: pass
            
        final_revisao = list(set(already_revising + sob_revisao))
        db.execute_query("UPDATE cidadaos SET campos_sob_revisao = ? WHERE cnf = ?", (json.dumps(final_revisao), cnf))
        
        flash("Sua solicitação de privacidade foi enviada e os dados já foram ocultados para análise!", "success")
    except Exception as e:
        flash(f"Erro ao processar solicitação: {e}", "error")
        
    return redirect(url_for('perfil', cnf=cnf))

@app.errorhandler(403)
def access_denied(e):
    return "Acesso Negado", 403

@app.errorhandler(404)
def page_not_found(e):
    return "Erro 404 - Página não encontrada", 404

@app.route('/lang/<lang>')
def set_language(lang):
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 20002))
    app.run(host='0.0.0.0', port=port, debug=True)
