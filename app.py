import os
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database.db_manager import DatabaseManager
from utils.security import sanitizar_input, formatar_data_sp
from utils.logic import gerar_cnf, gerar_rgf, gerar_qrcode_base64
from datetime import datetime
from models.user import User
from utils.auth_utils import role_required
from utils.mfa import validar_totp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

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
    session.permanent = True
    
    if request.method == 'POST':
        for key in request.form:
            request.form = request.form.copy()
            request.form[key] = sanitizar_input(request.form[key])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_val = request.form.get('cnf')
        if query_val:
            # Tentar buscar por CNF exato ou busca parcial por Nome
            db = DatabaseManager()
            res = db.execute_query("SELECT cnf FROM cidadaos WHERE cnf = ? OR nome LIKE ?", (query_val, f"%{query_val}%"), fetchone=True)
            if res:
                return redirect(url_for('perfil', cnf=res['cnf']))
            else:
                from flask import flash
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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.find_by_email(email)
        if user and user.check_password(password):
            # Salva ID do usuário na sessão temporária para o próximo passo
            session['pending_user_id'] = user.id
            
            # Só exige MFA se o segredo estiver cadastrado para este usuário
            if user.totp_secret:
                return redirect(url_for('login_mfa'))
            
            # Sem MFA cadastrada, login direto
            login_user(user)
            session.pop('pending_user_id', None)
            return redirect(url_for('index'))
        
        return "Credenciais inválidas", 401
    
    return render_template('login.html')

@app.route('/login/mfa', methods=['GET', 'POST'])
def login_mfa():
    user_id = session.get('pending_user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        token = request.form.get('token')
        user = User.get(user_id)
        
        # Valida contra o segredo salvo no banco para este usuário
        if user and user.totp_secret and validar_totp(user.totp_secret, token):
            login_user(user)
            session.pop('pending_user_id', None)
            return redirect(url_for('index'))
        
        return "Token MFA Inválido", 401
        
    return render_template('login_mfa.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/perfil/<cnf>')
def perfil(cnf):
    cidadao = db.execute_query("SELECT * FROM cidadaos WHERE cnf = ?", (cnf,), fetchone=True)
    if not cidadao:
        return "Cidadão não encontrado", 404
    
    # Lógica de Censura
    exibir_tudo = False
    if current_user.is_authenticated:
        if current_user.cargo in ['ADMIN', 'ANALISTA']:
            exibir_tudo = True
        elif current_user.cnf_vinculado == cnf:
            exibir_tudo = True
            
    # Processar dados censurados
    dados = dict(cidadao)
    if not exibir_tudo:
        if dados['regiao'] != 'DELETADA POR SOLICITAÇÃO':
            dados['regiao'] = "Logue para mais detalhes"
            
    return render_template('perfil.html', cidadao=dados, exibir_tudo=exibir_tudo)

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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cargo = request.form.get('cargo')
        cnf = request.form.get('cnf')
        
        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash(password)
        
        query = "INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado) VALUES (?, ?, ?, ?)"
        try:
            db.execute_query(query, (email, pwd_hash, cargo, cnf or None))
            return redirect(url_for('admin_usuarios'))
        except Exception as e:
            return f"Erro ao criar usuário: {e}", 400
            
    usuarios = db.execute_query("SELECT * FROM usuarios_sistema", fetchall=True)
    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/editar/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_usuario_editar(user_id):
    cargo = request.form.get('cargo')
    cnf = request.form.get('cnf')
    
    query = "UPDATE usuarios_sistema SET cargo = ?, cnf_vinculado = ? WHERE id = ?"
    db.execute_query(query, (cargo, cnf or None, user_id))
    from flask import flash
    flash("Configurações do usuário atualizadas com sucesso.", "success")
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuario/excluir/<int:user_id>')
@login_required
@role_required(['ADMIN'])
def admin_usuario_excluir(user_id):
    # Soft delete nos logs (is_uninstalled ou similar), mas aqui deletamos o acesso
    db.execute_query("DELETE FROM usuarios_sistema WHERE id = ?", (user_id,))
    from flask import flash
    flash("Usuário removido do sistema.", "warning")
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/emitir', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def admin_emitir():
    if request.method == 'POST':
        nome = request.form.get('nome')
        especie = request.form.get('especie')
        regiao = request.form.get('regiao')
        email = request.form.get('email') # Agora opcional
        foto_base64_raw = request.form.get('foto_base64') # Recebido do Cropper.js
        
        # 1. Verificar Duplicidade (Nome Completo ou E-mail)
        check_query = "SELECT id FROM cidadaos WHERE (nome = ? AND especie = ?) OR (email IS NOT NULL AND email = ?)"
        duplicate = db.execute_query(check_query, (nome, especie, email), fetchone=True)
        if duplicate:
            from flask import flash
            flash("Erro: Já existe um cidadão registrado com este Nome/Espécie ou E-mail.", "error")
            return redirect(url_for('admin_emitir'))

        query = """INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, qrcode_base64, foto_base64)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = (cnf, rgf, nome, especie, regiao, email, data_emissao, data_expiracao, qr_base64, foto_base64)
        
        try:
            db.execute_query(query, params)
            
            # 2. Criar conta automática em estado PENDENTE
            if email:
                from werkzeug.security import generate_password_hash
                import secrets
                # Senha temporária aleatória (será resetada no primeiro acesso)
                temp_pass = secrets.token_urlsafe(12)
                pwd_hash = generate_password_hash(temp_pass)
                
                db.execute_query(
                    "INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado, status) VALUES (?, ?, ?, ?, ?)",
                    (email, pwd_hash, 'USUARIO', cnf, 'PENDENTE')
                )

                # 3. Disparar E-mail Detalhado (Fase 7)
                user_data = {
                    'nome': nome,
                    'cnf': cnf,
                    'rgf': rgf,
                    'email': email,
                    'temp_pass': temp_pass
                }
                send_welcome_email(user_data)
                
            return redirect(url_for('perfil', cnf=cnf))
        except Exception as e:
            return f"Erro ao emitir documento: {e}", 500
            
    return render_template('admin_emitir.html')

@app.route('/ativar-conta', methods=['GET', 'POST'])
@login_required
def ativar_conta():
    if current_user.status != 'PENDENTE':
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        nova_senha = request.form.get('password')
        conf_senha = request.form.get('confirm_password')
        
        if nova_senha != conf_senha:
            from flask import flash
            flash("As senhas não coincidem.", "error")
            return render_template('ativar_conta.html')
            
        # 1. Atualizar Senha e Ativar Status
        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash(nova_senha)
        db.execute_query("UPDATE usuarios_sistema SET senha_hash = ?, status = 'ATIVO' WHERE id = ?", (pwd_hash, current_user.id))
        
        # 2. Forçar Configuração de MFA (Redirecionar para perfil onde tem o botão de gerar QR)
        from flask import flash
        flash("Senha atualizada! Agora, ative seu MFA para segurança total.", "success")
        return redirect(url_for('perfil', cnf=current_user.cnf_vinculado))
        
    return render_template('ativar_conta.html')

@app.route('/admin/registros')
@login_required
@role_required(['ADMIN', 'ANALISTA'])
def admin_registros():
    registros = db.execute_query("SELECT * FROM cidadaos ORDER BY id DESC", fetchall=True)
    return render_template('admin_registros.html', registros=registros)

@app.errorhandler(403)
def access_denied(e):
    return "Acesso Negado", 403

@app.errorhandler(404)
def page_not_found(e):
    return "Erro 404 - Página não encontrada", 404

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 6969))
    app.run(host='0.0.0.0', port=port, debug=True)
