import os
import sys
import json
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.utils.config import Config
from shared.utils.security import sanitizar_input, formatar_data_sp, role_required
from shared.utils.identity import gerar_cnf, gerar_rgf, gerar_qrcode_base64
from shared.utils.mfa import validar_totp
from shared.utils.email_service import send_welcome_email
from shared.utils.cross_db import create_pre_account_social, sync_social_account

from database.db_manager import DatabaseManager
from models.user import User

try:
    from core_i18n import configure_i18n
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core_i18n import configure_i18n

load_dotenv()

app = Flask(__name__)
configure_i18n(app)
app.config["SECRET_KEY"] = Config.SECRET_KEY_CGRF
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

csrf = CSRFProtect(app)
db = DatabaseManager()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@app.template_filter("from_json")
def from_json_filter(s):
    try:
        return json.loads(s)
    except Exception:
        return {}


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.before_request
def monitor_session():
    session.permanent = True
    if request.method == "POST":
        for key in request.form:
            request.form = request.form.copy()
            request.form[key] = sanitizar_input(request.form[key])


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query_val = request.form.get("cnf")
        if query_val:
            res = db.execute_query(
                "SELECT cnf FROM cidadaos WHERE (cnf = ? OR nome LIKE ?) AND is_valido = 1",
                (query_val, f"%{query_val}%"),
                fetchone=True,
            )
            if res:
                return redirect(url_for("perfil", cnf=res["cnf"]))
            else:
                flash("Cidadão não encontrado na base de dados.", "error")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.find_by_email(email)
        if user and user.check_password(password):
            login_user(user)

            if user.status == "PENDENTE":
                return redirect(url_for("ativar_conta"))

            if user.totp_secret:
                session["mfa_pending_user_id"] = user.id
                logout_user()
                return redirect(url_for("login_mfa"))

            return redirect(
                url_for("perfil", cnf=user.cnf_vinculado) if user.cargo == "USUARIO" else url_for("index")
            )

        flash("Credenciais inválidas ou conta inexistente.", "error")

    return render_template("login.html")


@app.route("/login/mfa", methods=["GET", "POST"])
def login_mfa():
    user_id = session.get("mfa_pending_user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "POST":
        token = request.form.get("token")
        user = User.get(user_id)

        if user and user.totp_secret and validar_totp(user.totp_secret, token):
            login_user(user)
            session.pop("mfa_pending_user_id", None)
            return redirect(url_for("index"))

        flash("Token MFA Inválido ou expirado.", "error")

    return render_template("login_mfa.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/perfil/<cnf>")
def perfil(cnf):
    cidadao = db.execute_query(
        "SELECT * FROM cidadaos WHERE cnf = ? AND is_valido = 1", (cnf,), fetchone=True
    )
    if not cidadao:
        flash("Identidade digital não encontrada ou inativa.", "error")
        return redirect(url_for("index"))

    cidadao = dict(cidadao)

    exibir_tudo = False
    if current_user.is_authenticated:
        if current_user.cargo in ["ADMIN", "ANALISTA"]:
            exibir_tudo = True
        elif current_user.cnf_vinculado == cnf:
            exibir_tudo = True

    sob_revisao = []
    if cidadao.get("campos_sob_revisao"):
        try:
            sob_revisao = json.loads(cidadao["campos_sob_revisao"])
        except Exception:
            sob_revisao = []

    if not exibir_tudo:
        for campo in sob_revisao:
            if campo in cidadao:
                cidadao[campo] = "[ DADO SOB REVISÃO (LGPD) ]"
            if campo == "foto":
                cidadao["foto_base64"] = None

    return render_template("perfil.html", cidadao=cidadao, exibir_tudo=exibir_tudo, sob_revisao=sob_revisao)


@app.route("/admin/usuarios", methods=["GET", "POST"])
@login_required
@role_required(["ADMIN"])
def admin_usuarios():
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/users")


@app.route("/admin/emitir", methods=["GET", "POST"])
@login_required
@role_required(["ADMIN"])
def admin_emitir():
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/emit")


@app.route("/admin/registros")
@login_required
@role_required(["ADMIN", "ANALISTA"])
def admin_registros():
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/records")


@app.route("/admin/privacidade")
@login_required
@role_required(["ADMIN"])
def admin_privacidade():
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/privacy")


@app.route("/admin/usuario/editar/<int:user_id>", methods=["POST"])
@login_required
@role_required(["ADMIN"])
def admin_usuario_editar(user_id):
    cargo = request.form.get("cargo")
    cnf = request.form.get("cnf")
    query = "UPDATE usuarios_sistema SET cargo = ?, cnf_vinculado = ? WHERE id = ?"
    db.execute_query(query, (cargo, cnf or None, user_id))
    flash("Configurações atualizadas.", "success")
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/users")


@app.route("/admin/usuario/excluir/<int:user_id>", methods=["POST"])
@login_required
@role_required(["ADMIN"])
def admin_usuario_excluir(user_id):
    db.execute_query("UPDATE usuarios_sistema SET status = 'INATIVO' WHERE id = ?", (user_id,))
    flash("Usuário desativado.", "warning")
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/users")


@app.route("/admin/usuario/reenviar-email/<int:user_id>")
@login_required
@role_required(["ADMIN"])
def admin_usuario_reenviar_email_redir(user_id):
    return redirect(f"https://{Config.ADMIN_DOMAIN}/cgrf/user/resend/{user_id}")


@app.route("/ativar-conta", methods=["GET", "POST"])
@login_required
def ativar_conta():
    if current_user.status != "PENDENTE":
        return redirect(url_for("index"))
    if request.method == "POST":
        nova_senha = request.form.get("password")
        conf_senha = request.form.get("confirm_password")
        if nova_senha != conf_senha:
            flash("As senhas não coincidem.", "error")
            return render_template("ativar_conta.html")
        pwd_hash = generate_password_hash(nova_senha)
        db.execute_query(
            "UPDATE usuarios_sistema SET senha_hash = ?, status = 'ATIVO' WHERE id = ?",
            (pwd_hash, current_user.id),
        )
        sync_social_account(current_user.email, current_user.email, status="ATIVO", password_hash=pwd_hash)
        flash("Sua conta foi ativada com sucesso!", "success")
        return redirect(url_for("perfil", cnf=current_user.cnf_vinculado))
    return render_template("ativar_conta.html")


@app.route("/solicitar-privacidade", methods=["POST"])
@login_required
def solicitar_privacidade():
    cnf = current_user.cnf_vinculado
    if not cnf:
        flash("Sua conta não possui uma CNF vinculada para gerenciar privacidade.", "error")
        return redirect(url_for("index"))

    acoes = {}
    sob_revisao = []

    campos = ["nome", "especie", "regiao", "foto"]
    for campo in campos:
        action = request.form.get(f"action_{campo}", "none")
        if action != "none":
            acoes[campo] = {"acao": action, "novo_valor": request.form.get(f"value_{campo}")}
            sob_revisao.append(campo)

    if request.form.get("delete_all") == "1":
        acoes["delete_all"] = True

    if not acoes:
        flash("Nenhuma alteração solicitada.", "warning")
        return redirect(url_for("perfil", cnf=cnf))

    try:
        query_ticket = """INSERT INTO solicitacoes_privacidade (cnf_solicitante, tipo_acao, detalhes_json, data_solicitacao)
                          VALUES (?, ?, ?, ?)"""
        db.execute_query(
            query_ticket,
            (
                cnf,
                "REMOVER" if "delete_all" in acoes else "ALTERAR",
                json.dumps(acoes),
                datetime.now().strftime("%d/%m/%Y %H:%M"),
            ),
        )

        curr_reg = db.execute_query(
            "SELECT campos_sob_revisao FROM cidadaos WHERE cnf = ?", (cnf,), fetchone=True
        )
        already_revising = []
        if curr_reg and curr_reg["campos_sob_revisao"]:
            try:
                already_revising = json.loads(curr_reg["campos_sob_revisao"])
            except Exception:
                pass

        final_revisao = list(set(already_revising + sob_revisao))
        db.execute_query(
            "UPDATE cidadaos SET campos_sob_revisao = ? WHERE cnf = ?",
            (json.dumps(final_revisao), cnf),
        )

        flash("Sua solicitação de privacidade foi enviada e os dados já foram ocultados para análise!", "success")
    except Exception as e:
        flash(f"Erro ao processar solicitação: {e}", "error")

    return redirect(url_for("perfil", cnf=cnf))


@app.errorhandler(403)
def access_denied(e):
    return render_template("index.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("index.html"), 404


@app.route("/lang/<lang>")
def set_language(lang):
    if lang in ["pt", "en", "es"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 20002))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
