import os
import sys
import sqlite3
import urllib.request
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.utils.config import Config
from shared.utils.identity import gerar_cnf, gerar_rgf, gerar_qrcode_base64
from shared.utils.email_service import send_welcome_email
from shared.utils.cross_db import create_pre_account_social, deactivate_account_everywhere, check_email_conflicts

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY_ADMIN
csrf = CSRFProtect(app)

DB_PATHS = Config.DB_PATHS
LOG_PATH = "/app/shared_logs/access_log.log"

ADMIN_DB_PATH = "database/admin_panel.db"

ALLOWED_TABLES = {
    "cgrf": ["cidadaos", "usuarios_sistema", "solicitacoes_privacidade"],
    "pawsteps": [
        "users", "events", "posts", "stories", "messages",
        "follows", "location_pins", "post_likes", "post_saves", "post_reposts",
    ],
    "shop": ["products", "orders", "order_items", "users"],
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


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
    if not os.path.exists("database"):
        os.makedirs("database")
    conn = get_admin_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        must_change_password BOOLEAN DEFAULT 1
    )"""
    )
    user = conn.execute("SELECT * FROM admin_users WHERE username = ?", ("Luke_Arwolf",)).fetchone()
    if not user:
        initial_pass = os.getenv("ADMIN_INITIAL_PASSWORD", secrets.token_urlsafe(16))
        hashed = generate_password_hash(initial_pass)
        conn.execute(
            "INSERT INTO admin_users (username, password, must_change_password) VALUES (?, ?, 1)",
            ("Luke_Arwolf", hashed),
        )
        print(f"[ADMIN BOOTSTRAP] Initial admin created. Password: {initial_pass}")
        print("[ADMIN BOOTSTRAP] Change this password immediately on first login.")
    conn.commit()
    conn.close()


init_admin_db()


@login_manager.user_loader
def load_user(user_id):
    conn = get_admin_db()
    user = conn.execute("SELECT * FROM admin_users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return AdminUser(user["id"], user["username"], user["must_change_password"])
    return None


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        conn = get_admin_db()
        user = conn.execute("SELECT * FROM admin_users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            admin_user = AdminUser(user["id"], user["username"], user["must_change_password"])
            login_user(admin_user)
            if admin_user.must_change:
                return redirect(url_for("change_password"))
            return redirect(url_for("index"))
        flash("Credenciais inválidas.", "danger")
    return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        hashed = generate_password_hash(new_password)
        conn = get_admin_db()
        conn.execute(
            "UPDATE admin_users SET password = ?, must_change_password = 0 WHERE id = ?",
            (hashed, current_user.id),
        )
        conn.commit()
        conn.close()
        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for("index"))
    return render_template("change_password.html")


@app.route("/")
@login_required
def index():
    if current_user.must_change:
        return redirect(url_for("change_password"))
    return render_template("index.html", active_page="index")


@app.route("/api/stats")
@login_required
def get_stats():
    stats = {
        "total_requests": 0,
        "status_200": 0,
        "status_404": 0,
        "status_500": 0,
        "recent_ips": [],
        "security_alerts": [],
        "db_counts": {},
    }

    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r") as f:
                lines = f.readlines()[-500:]
                stats["total_requests"] = len(lines)
                for line in lines:
                    if " 200 " in line:
                        stats["status_200"] += 1
                    elif " 404 " in line:
                        stats["status_404"] += 1
                    elif " 500 " in line or " 502 " in line:
                        stats["status_500"] += 1

                    if ".env" in line or "wp-admin" in line or "config" in line:
                        stats["security_alerts"].append(f"Tentativa suspeita detectada: {line[:50]}...")
        except Exception:
            pass

    for app_name in DB_PATHS:
        db_path = Config.get_db_path(app_name)
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                count = 0
                for t in tables:
                    if t != "sqlite_sequence":
                        try:
                            count += conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
                        except Exception:
                            pass
                stats["db_counts"][app_name] = count
                conn.close()
            except Exception:
                stats["db_counts"][app_name] = -1

    return jsonify(stats)


@app.route("/api/health")
@login_required
def get_health():
    services = {
        "cgrf": {"host": "furry_cgrf", "port": 20002, "domain": "cgrf.com.br"},
        "pawsteps": {"host": "furry_pawsteps", "port": 20001, "domain": "pawsteps.social"},
        "shop": {"host": "furry_shop", "port": 20003, "domain": "furrycore.com.br/shop"},
        "landing": {"host": "furry_landing", "port": 20000, "domain": "furrycore.com.br"},
    }
    result = {}
    for name, svc in services.items():
        try:
            url = f"http://{svc['host']}:{svc['port']}/"
            req = urllib.request.Request(url, method="HEAD")
            resp = urllib.request.urlopen(req, timeout=3)
            result[name] = {"status": "online", "code": resp.getcode(), "domain": svc["domain"]}
        except Exception:
            result[name] = {"status": "offline", "code": 0, "domain": svc["domain"]}
    return jsonify(result)


@app.route("/database/<app_name>")
@login_required
def view_db(app_name):
    if app_name not in DB_PATHS:
        return "App não encontrado", 404

    db_path = Config.get_db_path(app_name)
    if not os.path.exists(db_path):
        return f"Banco de dados de {app_name} não encontrado no path mapeado.", 404

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    conn.close()

    return render_template("view_db.html", app_name=app_name, tables=tables)


@app.route("/database/<app_name>/<table>")
@login_required
def view_table(app_name, table):
    if app_name not in ALLOWED_TABLES:
        flash("Aplicação inválida.", "danger")
        return redirect(url_for("index"))

    if table not in ALLOWED_TABLES[app_name]:
        flash("Tabela não autorizada.", "danger")
        return redirect(url_for("view_db", app_name=app_name))

    db_path = Config.get_db_path(app_name)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    show_deleted = request.args.get("show_deleted", "0") == "1"

    cursor_info = conn.execute(f"PRAGMA table_info([{table}])")
    cols_info = cursor_info.fetchall()
    col_names = [c[1] for c in cols_info]

    soft_col = None
    for sc in ["is_valido", "status", "ativo", "active", "is_uninstalled"]:
        if sc in col_names:
            soft_col = sc
            break

    if soft_col and not show_deleted:
        if soft_col in ("is_valido", "ativo", "active"):
            query = f"SELECT * FROM [{table}] WHERE [{soft_col}] = 1 ORDER BY rowid DESC LIMIT 200"
        elif soft_col == "is_uninstalled":
            query = f"SELECT * FROM [{table}] WHERE [{soft_col}] = 0 ORDER BY rowid DESC LIMIT 200"
        elif soft_col == "status":
            query = f"SELECT * FROM [{table}] WHERE [{soft_col}] != 'INATIVO' ORDER BY rowid DESC LIMIT 200"
        else:
            query = f"SELECT * FROM [{table}] ORDER BY rowid DESC LIMIT 200"
    else:
        query = f"SELECT * FROM [{table}] ORDER BY rowid DESC LIMIT 200"

    data = conn.execute(query).fetchall()
    columns = data[0].keys() if data else col_names
    conn.close()
    return render_template("view_table.html", app_name=app_name, table=table, columns=columns, data=data, show_deleted=show_deleted, soft_col=soft_col)


@app.route("/security")
@login_required
def view_security():
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()[-100:]
            for line in lines:
                if any(x in line for x in [".env", "wp-admin", "config", "phpinfo", "403", "404"]):
                    logs.append(line)
    return render_template("security.html", logs=logs)


@app.route("/admins")
@login_required
def manage_admins():
    conn = get_admin_db()
    dash_admins = conn.execute("SELECT * FROM admin_users").fetchall()
    conn.close()

    app_admins = {}
    for app_name, path_key in DB_PATHS.items():
        db_path = Config.get_db_path(app_name)
        if os.path.exists(db_path):
            try:
                conn_app = sqlite3.connect(db_path)
                conn_app.row_factory = sqlite3.Row
                tables = [
                    t[0]
                    for t in conn_app.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]
                if "users" in tables:
                    cols = [
                        c[1]
                        for c in conn_app.execute("PRAGMA table_info(users)").fetchall()
                    ]
                    if "is_admin" in cols:
                        app_admins[app_name] = conn_app.execute(
                            "SELECT * FROM users WHERE is_admin = 1"
                        ).fetchall()
                conn_app.close()
            except Exception:
                app_admins[app_name] = []

    return render_template("admins.html", dash_admins=dash_admins, app_admins=app_admins)


@app.route("/admins/add", methods=["POST"])
@login_required
def add_admin():
    username = request.form.get("username")
    password = generate_password_hash(request.form.get("password"))
    conn = get_admin_db()
    try:
        conn.execute(
            "INSERT INTO admin_users (username, password, must_change_password) VALUES (?, ?, ?)",
            (username, password, 0),
        )
        conn.commit()
        flash(f"Admin {username} criado com sucesso.", "success")
    except Exception:
        flash("Erro ao criar admin (usuário já existe?)", "danger")
    conn.close()
    return redirect(url_for("manage_admins"))


@app.route("/admins/delete/<int:admin_id>", methods=["POST"])
@login_required
def delete_admin(admin_id):
    if admin_id == int(current_user.id):
        flash("Você não pode deletar a si mesmo!", "danger")
        return redirect(url_for("manage_admins"))
    conn = get_admin_db()
    conn.execute("DELETE FROM admin_users WHERE id = ?", (admin_id,))
    conn.commit()
    conn.close()
    flash("Admin removido.", "info")
    return redirect(url_for("manage_admins"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/cgrf/users", methods=["GET", "POST"])
@login_required
def cgrf_manage_users():
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        cargo = request.form.get("cargo")
        cnf = request.form.get("cnf")
        try:
            conn.execute(
                "INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado, status) VALUES (?, ?, ?, ?, 'ATIVO')",
                (email, password, cargo, cnf or None),
            )
            conn.commit()
            flash(f"Usuário {email} criado no CGRF.", "success")
        except Exception as e:
            flash(f"Erro ao criar usuário: {e}", "danger")

    usuarios = conn.execute(
        "SELECT * FROM usuarios_sistema WHERE cargo IN ('ADMIN', 'ANALISTA') AND status = 'ATIVO'"
    ).fetchall()
    conn.close()
    return render_template("cgrf_users.html", usuarios=usuarios)


@app.route("/cgrf/emit", methods=["GET", "POST"])
@login_required
def cgrf_emit_wallet():
    if request.method == "POST":
        nome = request.form.get("nome")
        especie = request.form.get("especie")
        regiao = request.form.get("regiao")
        cidade = request.form.get("cidade")
        pais = request.form.get("pais", "Brasil")
        idiomas_list = request.form.getlist("idiomas")
        idiomas = ", ".join(idiomas_list) if idiomas_list else "Não Informado"
        email = request.form.get("email")
        foto_base64_raw = request.form.get("foto_base64")
        confirmed_link = request.form.get("confirmed_link") == "true"

        if email and not confirmed_link:
            conflicts = check_email_conflicts(email)
            if conflicts:
                return render_template(
                    "cgrf_confirm_link.html",
                    conflicts=conflicts,
                    form_data=request.form.to_dict(flat=False),
                )

        cnf = gerar_cnf()
        rgf = gerar_rgf()
        qr_base64 = gerar_qrcode_base64(cnf)

        foto_base64 = None
        if foto_base64_raw and "," in foto_base64_raw:
            foto_base64 = foto_base64_raw.split(",")[1]

        hoje = datetime.now()
        exp = hoje.replace(year=hoje.year + 10)

        db_path = Config.get_db_path("cgrf")
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """INSERT INTO cidadaos (cnf, rgf, nome, especie, regiao, cidade, pais, idiomas, email, data_emissao, data_expiracao, qrcode_base64, foto_base64)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cnf, rgf, nome, especie, regiao, cidade, pais, idiomas, email,
                    hoje.strftime("%d/%m/%Y"), exp.strftime("%d/%m/%Y"), qr_base64, foto_base64,
                ),
            )

            if email:
                temp_pass = secrets.token_urlsafe(12)
                pwd_hash = generate_password_hash(temp_pass)
                conn.execute(
                    "INSERT INTO usuarios_sistema (email, senha_hash, cargo, cnf_vinculado, status) VALUES (?, ?, ?, ?, ?)",
                    (email, pwd_hash, "USUARIO", cnf, "PENDENTE"),
                )

                user_data = {"nome": nome, "cnf": cnf, "rgf": rgf, "email": email, "temp_pass": temp_pass}
                success, mail_err = send_welcome_email(user_data)
                if not success:
                    print(f"[SMTP FAIL] Wallet emission email failed: {mail_err}")

                create_pre_account_social(email, nome)

            conn.commit()
            flash(f"Carteira de {nome} emitida com sucesso! CNF: {cnf}", "success")
        except Exception as e:
            print(f"[DATABASE ERROR] CGRF emission failed: {e}")
            flash(f"Erro na emissão: {e}", "danger")
        finally:
            conn.close()
        return redirect(url_for("cgrf_manage_records"))

    return render_template("cgrf_emitir.html")


@app.route("/cgrf/records")
@login_required
def cgrf_manage_records():
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    registros = conn.execute("SELECT * FROM cidadaos WHERE is_valido = 1 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("cgrf_registros.html", registros=registros)


@app.route("/cgrf/privacy")
@login_required
def cgrf_manage_privacy():
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
    SELECT s.rowid as id, s.*, c.nome as nome_cidadao
    FROM solicitacoes_privacidade s
    JOIN cidadaos c ON s.cnf_solicitante = c.cnf
    WHERE s.status = 'PENDENTE'
    ORDER BY s.data_solicitacao ASC
    """
    solicitacoes = conn.execute(query).fetchall()
    conn.close()
    return render_template("cgrf_privacidade.html", solicitacoes=solicitacoes, active_page="cgrf_privacy")


@app.route("/cgrf/delete/<cnf>", methods=["POST"])
@login_required
def cgrf_delete_record(cnf):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE cidadaos SET is_valido = 0 WHERE cnf = ?", (cnf,))
        reg = conn.execute("SELECT email FROM cidadaos WHERE cnf = ?", (cnf,)).fetchone()
        if reg and reg[0]:
            deactivate_account_everywhere(reg[0])
        conn.commit()
        flash(f"Registro {cnf} e acessos vinculados inativados com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao inativar registro: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("cgrf_manage_records"))


@app.route("/cgrf/resend_email/<cnf>")
@login_required
def cgrf_resend_email(cnf):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    reg = conn.execute("SELECT * FROM cidadaos WHERE cnf = ?", (cnf,)).fetchone()
    conn.close()

    if reg and reg["email"]:
        user_data = {
            "nome": reg["nome"],
            "cnf": reg["cnf"],
            "rgf": reg["rgf"],
            "email": reg["email"],
            "temp_pass": "Consulte sua senha anterior",
        }
        success, mail_err = send_welcome_email(user_data)
        if success:
            flash(f"E-mail de boas-vindas reenviado para {reg['email']}.", "success")
        else:
            flash(f"Falha ao reenviar e-mail: {mail_err}", "danger")
    else:
        flash("Registro não encontrado ou e-mail ausente.", "warning")
    return redirect(url_for("cgrf_manage_records"))


@app.route("/cgrf/resend_user_email/<email>")
@login_required
def cgrf_resend_user_email(email):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    reg = conn.execute("SELECT * FROM cidadaos WHERE email = ?", (email,)).fetchone()
    conn.close()

    if reg:
        user_data = {
            "nome": reg["nome"],
            "cnf": reg["cnf"],
            "rgf": reg["rgf"],
            "email": reg["email"],
            "temp_pass": "Consulte sua senha anterior",
        }
        success, mail_err = send_welcome_email(user_data)
        if success:
            flash(f"E-mail de boas-vindas reenviado para {email}.", "success")
        else:
            flash(f"Falha ao reenviar: {mail_err}", "danger")
    else:
        flash(
            f"Registro detalhado não encontrado para {email}. Somente usuários vinculados a um CNF podem receber o e-mail de boas-vindas completo.",
            "warning",
        )

    return redirect(url_for("cgrf_manage_users"))


@app.route("/cgrf/edit/<cnf>", methods=["GET", "POST"])
@login_required
def cgrf_edit_record(cnf):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        nome = request.form.get("nome")
        especie = request.form.get("especie")
        cidade = request.form.get("cidade")
        pais = request.form.get("pais")
        try:
            conn.execute(
                "UPDATE cidadaos SET nome = ?, especie = ?, cidade = ?, pais = ? WHERE cnf = ?",
                (nome, especie, cidade, pais, cnf),
            )
            conn.commit()
            flash(f"Dados do registro {cnf} atualizados.", "success")
            return redirect(url_for("cgrf_manage_records"))
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "danger")

    reg = conn.execute("SELECT * FROM cidadaos WHERE cnf = ?", (cnf,)).fetchone()
    conn.close()
    if not reg:
        flash("Registro não encontrado.", "danger")
        return redirect(url_for("cgrf_manage_records"))

    return render_template("cgrf_editar.html", reg=reg)


@app.route("/database/edit/<app_name>/<table_name>/<int:row_id>", methods=["GET", "POST"])
@login_required
def generic_edit(app_name, table_name, row_id):
    if app_name not in ALLOWED_TABLES:
        flash("Aplicação inválida.", "danger")
        return redirect(url_for("index"))
    if table_name not in ALLOWED_TABLES[app_name]:
        flash("Tabela não autorizada.", "danger")
        return redirect(url_for("view_db", app_name=app_name))

    db_path = Config.get_db_path(app_name)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
    columns_info = cursor.fetchall()
    pk_col = next((c[1] for c in columns_info if c[5] == 1), "id")
    editable_cols = [c[1] for c in columns_info if c[1] != pk_col and c[1] not in ("password", "senha_hash", "qrcode_base64", "foto_base64")]

    if request.method == "POST":
        try:
            updates = []
            values = []
            for col in editable_cols:
                val = request.form.get(col)
                if val is not None:
                    updates.append(f"[{col}] = ?")
                    values.append(val)
            values.append(row_id)
            conn.execute(f"UPDATE [{table_name}] SET {', '.join(updates)} WHERE [{pk_col}] = ?", values)
            conn.commit()
            flash(f"Registro #{row_id} atualizado com sucesso.", "success")
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "danger")
        finally:
            conn.close()
        return redirect(url_for("view_table", app_name=app_name, table=table_name))

    row = conn.execute(f"SELECT * FROM [{table_name}] WHERE [{pk_col}] = ?", (row_id,)).fetchone()
    conn.close()
    if not row:
        flash("Registro não encontrado.", "danger")
        return redirect(url_for("view_table", app_name=app_name, table=table_name))

    return render_template("generic_edit.html", app_name=app_name, table=table_name, row_id=row_id, row=row, columns=editable_cols, pk_col=pk_col)


@app.route("/database/delete/<app_name>/<table_name>/<int:row_id>", methods=["POST"])
@login_required
def generic_delete(app_name, table_name, row_id):
    if app_name not in ALLOWED_TABLES:
        flash("Aplicação inválida.", "danger")
        return redirect(url_for("index"))

    if table_name not in ALLOWED_TABLES[app_name]:
        flash("Tabela não autorizada.", "danger")
        return redirect(url_for("index"))

    db_path = Config.get_db_path(app_name)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
        columns_info = cursor.fetchall()
        columns = [c[1] for c in columns_info]
        pk_col = next((c[1] for c in columns_info if c[5] == 1), "id")

        soft_delete_col = None
        for col in ["is_valido", "status", "ativo", "active", "is_uninstalled"]:
            if col in columns:
                soft_delete_col = col
                break

        if soft_delete_col:
            val = 0 if soft_delete_col in ["is_valido", "ativo", "active"] else "INATIVO"
            if soft_delete_col == "is_uninstalled":
                val = 1
            conn.execute(f"UPDATE [{table_name}] SET [{soft_delete_col}] = ? WHERE [{pk_col}] = ?", (val, row_id))
            flash(f"Registro inativado via Soft Delete (Tabela: {table_name}).", "success")
        else:
            flash(
                f"A tabela {table_name} não possui suporte para Soft Delete. Operação negada por segurança.",
                "warning",
            )

        conn.commit()
    except Exception as e:
        flash(f"Erro na operação: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("view_table", app_name=app_name, table=table_name))


@app.route("/database/toggle/<app_name>/<table_name>/<int:row_id>", methods=["POST"])
@login_required
def generic_toggle(app_name, table_name, row_id):
    if app_name not in ALLOWED_TABLES or table_name not in ALLOWED_TABLES[app_name]:
        flash("Operação não autorizada.", "danger")
        return redirect(url_for("index"))

    db_path = Config.get_db_path(app_name)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
        columns_info = cursor.fetchall()
        columns = [c[1] for c in columns_info]
        pk_col = next((c[1] for c in columns_info if c[5] == 1), "id")

        toggle_col = None
        for col in ["status", "ativo", "active"]:
            if col in columns:
                toggle_col = col
                break

        if toggle_col:
            current = conn.execute(f"SELECT [{toggle_col}] FROM [{table_name}] WHERE [{pk_col}] = ?", (row_id,)).fetchone()
            if current:
                cur_val = current[0]
                if toggle_col == "status":
                    new_val = "INATIVO" if cur_val == "ATIVO" else "ATIVO"
                else:
                    new_val = 0 if cur_val else 1
                conn.execute(f"UPDATE [{table_name}] SET [{toggle_col}] = ? WHERE [{pk_col}] = ?", (new_val, row_id))
                conn.commit()
                label = "ativado" if (new_val == "ATIVO" or new_val == 1) else "desativado"
                flash(f"Registro #{row_id} {label} com sucesso.", "success")
            else:
                flash("Registro não encontrado.", "danger")
        else:
            flash(f"Tabela {table_name} não suporta ativação/desativação.", "warning")
    except Exception as e:
        flash(f"Erro: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("view_table", app_name=app_name, table=table_name))


@app.route("/cgrf/privacy/approve/<int:request_id>", methods=["POST"])
@login_required
def cgrf_privacy_approve(request_id):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sol = conn.execute("SELECT rowid, * FROM solicitacoes_privacidade WHERE rowid = ?", (request_id,)).fetchone()
        if not sol:
            flash("Solicitação não encontrada.", "danger")
        else:
            tipo = sol["tipo_solicitacao"]
            cnf = sol["cnf_solicitante"]
            if tipo == "EXCLUSAO":
                conn.execute("UPDATE cidadaos SET is_valido = 0 WHERE cnf = ?", (cnf,))
                reg = conn.execute("SELECT email FROM cidadaos WHERE cnf = ?", (cnf,)).fetchone()
                if reg and reg["email"]:
                    deactivate_account_everywhere(reg["email"])
            elif tipo == "ANONIMIZACAO":
                conn.execute("UPDATE cidadaos SET nome = 'ANONIMIZADO', email = NULL, cidade = NULL WHERE cnf = ?", (cnf,))
            conn.execute("UPDATE solicitacoes_privacidade SET status = 'APROVADA', data_processamento = ? WHERE rowid = ?", (datetime.now().strftime("%d/%m/%Y %H:%M"), request_id))
            conn.commit()
            flash(f"Solicitação #{request_id} ({tipo}) aprovada com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao processar: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("cgrf_manage_privacy"))


@app.route("/cgrf/privacy/reject/<int:request_id>", methods=["POST"])
@login_required
def cgrf_privacy_reject(request_id):
    db_path = Config.get_db_path("cgrf")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE solicitacoes_privacidade SET status = 'REJEITADA', data_processamento = ? WHERE rowid = ?", (datetime.now().strftime("%d/%m/%Y %H:%M"), request_id))
        conn.commit()
        flash(f"Solicitação #{request_id} rejeitada.", "info")
    except Exception as e:
        flash(f"Erro ao rejeitar: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("cgrf_manage_privacy"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=29999, debug=Config.DEBUG)
