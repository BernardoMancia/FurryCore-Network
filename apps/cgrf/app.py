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
    flash("Configurações do usuário atualizadas com sucesso.", "success")
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuario/excluir/<int:user_id>')
@login_required
@role_required(['ADMIN'])
def admin_usuario_excluir(user_id):
    # Soft delete nos logs (is_uninstalled ou similar), mas aqui deletamos o acesso
    db.execute_query("DELETE FROM usuarios_sistema WHERE id = ?", (user_id,))
    flash("Usuário removido do sistema.", "warning")
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/usuario/reenviar-email/<int:user_id>')
@login_required
@role_required(['ADMIN'])
def admin_usuario_reenviar_email(user_id):
    """
    Gera uma nova senha temporária e reenvia as instruções de acesso ao usuário.
    """
    user = db.execute_query("SELECT * FROM usuarios_sistema WHERE id = ?", (user_id,), fetchone=True)
    if not user or not user['cnf_vinculado']:
        flash("Usuário não encontrado ou não possui CNF vinculado.", "error")
        return redirect(url_for('admin_usuarios'))
        
    cidadao = db.execute_query("SELECT * FROM cidadaos WHERE cnf = ?", (user['cnf_vinculado'],), fetchone=True)
    if not cidadao:
        flash("Cidadão vinculado não encontrado.", "error")
        return redirect(url_for('admin_usuarios'))
        
    # Gerar nova senha temporária
    import secrets
    temp_pass = secrets.token_urlsafe(12)
    pwd_hash = generate_password_hash(temp_pass)
    
    # Atualizar no banco
    db.execute_query("UPDATE usuarios_sistema SET senha_hash = ?, status = 'PENDENTE' WHERE id = ?", (pwd_hash, user_id))
    
    # Enviar e-mail
    user_data = {
        'nome': cidadao['nome'],
        'cnf': cidadao['cnf'],
        'rgf': cidadao['rgf'],
        'email': user['email'],
        'temp_pass': temp_pass
    }
    
    if send_welcome_email(user_data):
        flash(f"Instruções enviadas com sucesso para {user['email']}", "success")
    else:
        flash("Falha ao enviar e-mail. Verifique os logs do servidor.", "error")
        
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/emitir', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def admin_emitir():
    """
    Motor de emissão de novas credenciais com de-duplicação e auto-conta.
    """
    if request.method == 'POST':
        nome = request.form.get('nome')
        especie = request.form.get('especie')
        regiao = request.form.get('regiao')
        email = request.form.get('email')
        foto_base64_raw = request.form.get('foto_base64')
        
        # Gerar Identificadores e Datas
        cnf = gerar_cnf()
        rgf = gerar_rgf()
        qr_base64 = gerar_qrcode_base64(cnf)
        
        # Processar Foto
        foto_base64 = None
        if foto_base64_raw and "," in foto_base64_raw:
            foto_base64 = foto_base64_raw.split(",")[1]
            
        hoje = datetime.now()
        exp = hoje.replace(year=hoje.year + 10)
        data_emissao = formatar_data_sp(hoje)
        data_expiracao = formatar_data_sp(exp)
        
        # 1. Verificar Duplicidade apenas em registros ATIVOS
        check_query = "SELECT id FROM cidadaos WHERE ( (nome = ? AND especie = ?) OR (email IS NOT NULL AND email = ?) ) AND is_valido = 1"
        duplicate = db.execute_query(check_query, (nome, especie, email), fetchone=True)
        if duplicate:
            flash("Erro: Já existe um cidadão ATIVO registrado com este Nome/Espécie ou E-mail.", "error")
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
                
                # 3. Pre-criar conta na rede social
                create_pre_account_social(email, nome)
                
                if send_welcome_email(user_data):
                    flash(f"Documento emitido e instruções enviadas para {email}", "success")
                else:
                    flash("Documento emitido, mas houve falha ao enviar o e-mail. Tente reenviar manualmente na aba Usuários.", "warning")
                
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
            flash("As senhas não coincidem.", "error")
            return render_template('ativar_conta.html')
            
        # 1. Atualizar Senha e Ativar Status
        from werkzeug.security import generate_password_hash
        pwd_hash = generate_password_hash(nova_senha)
        db.execute_query("UPDATE usuarios_sistema SET senha_hash = ?, status = 'ATIVO' WHERE id = ?", (pwd_hash, current_user.id))
        
        # 2. Sincronizar e Ativar Conta Social (PawSteps)
        sync_social_account(current_user.email, current_user.email, status='ATIVO', password_hash=pwd_hash)

        # 3. Forçar Configuração de MFA (Redirecionar para perfil onde tem o botão de gerar QR)
        flash("Senha atualizada! Agora, ative seu MFA para segurança total. Sua conta social também está ativa!", "success")
        return redirect(url_for('perfil', cnf=current_user.cnf_vinculado))
        
    return render_template('ativar_conta.html')

@app.route('/admin/registros')
@login_required
@role_required(['ADMIN', 'ANALISTA'])
def admin_registros():
    """
    Lista todos os registros de cidadãos ativos para gestão.
    """
    registros = db.execute_query("SELECT * FROM cidadaos WHERE is_valido = 1 ORDER BY id DESC", fetchall=True)
    return render_template('admin_registros.html', registros=registros)

@app.route('/admin/registro/editar/<int:reg_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'ANALISTA'])
def admin_registro_editar(reg_id):
    nome = request.form.get('nome')
    especie = request.form.get('especie')
    regiao = request.form.get('regiao')
    email = request.form.get('email')
    
    print(f"[DEBUG] Editar ID {reg_id}: {nome}, {especie}, {email}")
    
    # 1. Buscar e-mail antigo para sincronização de conta
    old_data = db.execute_query("SELECT cnf, email FROM cidadaos WHERE id = ?", (reg_id,), fetchone=True)
    
    query = "UPDATE cidadaos SET nome = ?, especie = ?, regiao = ?, email = ? WHERE id = ?"
    db.execute_query(query, (nome, especie, regiao, email, reg_id))
    
    # 2. Sincronizar com tabela de usuários e Rede Social se o e-mail mudou
    if old_data and old_data['email'] != email:
        db.execute_query("UPDATE usuarios_sistema SET email = ? WHERE cnf_vinculado = ?", (email, old_data['cnf']))
        sync_social_account(old_data['email'], email)
    
    flash("Dados do cidadão atualizados com sucesso.", "success")
    return redirect(url_for('admin_registros'))

@app.route('/admin/registro/excluir/<int:reg_id>')
@login_required
@role_required(['ADMIN'])
def admin_registro_excluir(reg_id):
    """
    Desativa um registro (Soft Delete) e revoga acesso do usuário vinculado.
    """
    cidadao = db.execute_query("SELECT cnf FROM cidadaos WHERE id = ?", (reg_id,), fetchone=True)
    if cidadao:
        db.execute_query("UPDATE cidadaos SET is_valido = 0 WHERE id = ?", (reg_id,))
        db.execute_query("UPDATE usuarios_sistema SET status = 'INATIVO' WHERE cnf_vinculado = ?", (cidadao['cnf'],))
        flash("Registro desativado e acesso revogado com sucesso.", "warning")
    else:
        flash("Registro não encontrado.", "error")
        
    return redirect(url_for('admin_registros'))

# --- SISTEMA DE PRIVACIDADE (LGPD) ---

@app.route('/solicitar-privacidade', methods=['POST'])
@login_required
def solicitar_privacidade():
    """
    Processa solicitações de alteração ou exclusão de dados do cidadão titular.
    """
    import json
    from datetime import datetime
    
    cnf = current_user.cnf_vinculado
    if not cnf:
        flash("Nenhum registro vinculado para solicitar privacidade.", "error")
        return redirect(url_for('perfil', cnf='indefinido'))

    # 1. Verificar se é pedido de exclusão total
    delete_all = request.form.get('delete_all') == '1'
    
    if delete_all:
        # Registrar ticket de remoção total
        db.execute_query(
            "INSERT INTO solicitacoes_privacidade (cnf_solicitante, tipo_acao, status, data_solicitacao) VALUES (?, ?, ?, ?)",
            (cnf, 'REMOVER', 'PENDENTE', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        )
        flash("Solicitação de EXCLUSÃO TOTAL enviada para análise. Seus dados ficarão restritos.", "warning")
        return redirect(url_for('perfil', cnf=cnf))

    # 2. Processar campos específicos para alteração ou ocultação
    campos_alterar = {}
    campos_remover = []
    
    campos_mapeados = ['nome', 'especie', 'regiao', 'foto']
    
    for campo in campos_mapeados:
        acao = request.form.get(f'action_{campo}')
        if acao == 'alterar':
            valor = sanitizar_input(request.form.get(f'value_{campo}'))
            if valor:
                campos_alterar[campo] = valor
        elif acao == 'remover':
            campos_remover.append(campo)

    if not campos_alterar and not campos_remover:
        flash("Nenhuma alteração selecionada.", "info")
        return redirect(url_for('perfil', cnf=cnf))

    # 3. Registrar ticket de alteração parcial
    detalhes = {
        'alterar': campos_alterar,
        'remover': campos_remover
    }
    
    db.execute_query(
        "INSERT INTO solicitacoes_privacidade (cnf_solicitante, tipo_acao, detalhes_json, status, data_solicitacao) VALUES (?, ?, ?, ?, ?)",
        (cnf, 'ALTERAR', json.dumps(detalhes), 'PENDENTE', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    )
    
    # 4. Ocultação Temporária (LGPD Proof)
    # Lista de campos que não devem aparecer no perfil público até aprovação
    sob_revisao = list(campos_alterar.keys()) + campos_remover
    db.execute_query("UPDATE cidadaos SET campos_sob_revisao = ? WHERE cnf = ?", (json.dumps(sob_revisao), cnf))

    flash("Solicitações de privacidade enviadas! Os dados afetados ficarão ocultos para terceiros até a aprovação.", "success")
    return redirect(url_for('perfil', cnf=cnf))

@app.route('/admin/privacidade')
@login_required
@role_required(['ADMIN'])
def admin_privacidade():
    """
    Painel para administradores gerenciarem tickets de LGPD.
    """
    query = """
    SELECT s.*, c.nome as nome_cidadao 
    FROM solicitacoes_privacidade s
    JOIN cidadaos c ON s.cnf_solicitante = c.cnf
    WHERE s.status = 'PENDENTE'
    ORDER BY s.data_solicitacao ASC
    """
    solicitacoes = db.execute_query(query, fetchall=True)
    return render_template('admin_privacidade.html', solicitacoes=solicitacoes)

@app.route('/admin/privacidade/processar/<int:sol_id>', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def admin_privacidade_processar(sol_id):
    """
    Aprova ou rejeita uma solicitação de privacidade.
    """
    import json
    from utils.email_utils import send_privacy_status_email
    
    decisao = request.form.get('decisao') # 'APROVAR' ou 'REJEITAR'
    motivo = request.form.get('motivo', '')
    
    sol = db.execute_query("SELECT * FROM solicitacoes_privacidade WHERE id_solicitacao = ?", (sol_id,), fetchone=True)
    if not sol:
        flash("Solicitação não encontrada.", "error")
        return redirect(url_for('admin_privacidade'))
        
    cidadao = db.execute_query("SELECT * FROM cidadaos WHERE cnf = ?", (sol['cnf_solicitante'],), fetchone=True)
    
    if decisao == 'APROVAR':
        if sol['tipo_acao'] == 'REMOVER':
            # 1. EXCLUSÃO TOTAL (LGPD Direito ao Esquecimento)
            db.execute_query("DELETE FROM usuarios_sistema WHERE cnf_vinculado = ?", (sol['cnf_solicitante'],))
            db.execute_query("DELETE FROM cidadaos WHERE cnf = ?", (sol['cnf_solicitante'],))
            db.execute_query("DELETE FROM solicitacoes_privacidade WHERE cnf_solicitante = ?", (sol['cnf_solicitante'],))
            
            if cidadao and cidadao['email']:
                send_privacy_status_email(
                    cidadao['email'],
                    cidadao['nome'],
                    'APROVADO',
                    'REMOVER'
                )
            flash("Registro e conta excluídos permanentemente.", "success")
        
        else:
            # 2. ALTERAÇÃO PARCIAL
            detalhes = json.loads(sol['detalhes_json'])
            
            # Aplicar alterações
            for campo, valor in detalhes.get('alterar', {}).items():
                db.execute_query(f"UPDATE cidadaos SET {campo} = ? WHERE cnf = ?", (valor, sol['cnf_solicitante']))
            
            # Aplicar remoções (Setar null ou vazio)
            for campo in detalhes.get('remover', []):
                # Se for foto, setamos null
                if campo == 'foto':
                    db.execute_query("UPDATE cidadaos SET foto_base64 = NULL WHERE cnf = ?", (sol['cnf_solicitante'],))
                else:
                    db.execute_query(f"UPDATE cidadaos SET {campo} = 'Oculto pelo Usuário' WHERE cnf = ?", (sol['cnf_solicitante'],))
            
            # Limpar campos sob revisão
            db.execute_query("UPDATE cidadaos SET campos_sob_revisao = NULL WHERE cnf = ?", (sol['cnf_solicitante'],))
            db.execute_query("UPDATE solicitacoes_privacidade SET status = 'APROVADO' WHERE id_solicitacao = ?", (sol_id,))
            
            if cidadao and cidadao['email']:
                send_privacy_status_email(
                    cidadao['email'],
                    cidadao['nome'],
                    'APROVADO',
                    'ALTERAR'
                )
            flash("Solicitação aprovada e dados atualizados.", "success")
            
    else:
        # REJEITAR
        db.execute_query("UPDATE solicitacoes_privacidade SET status = 'REJEITADO', motivo_rejeicao = ? WHERE id_solicitacao = ?", (motivo, sol_id))
        # Restaurar visibilidade
        db.execute_query("UPDATE cidadaos SET campos_sob_revisao = NULL WHERE cnf = ?", (sol['cnf_solicitante'],))
        
        if cidadao and cidadao['email']:
            send_privacy_status_email(
                cidadao['email'],
                cidadao['nome'],
                'REJEITADO',
                sol['tipo_acao'],
                motivo=motivo
            )
        
        flash("Solicitação recusada e usuário notificado.", "info")

    return redirect(url_for('admin_privacidade'))

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
    port = int(os.getenv('APP_PORT', 6969))
    app.run(host='0.0.0.0', port=20002, debug=True)
