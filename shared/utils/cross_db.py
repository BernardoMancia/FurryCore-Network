import os
import sqlite3
import secrets
import random
from werkzeug.security import generate_password_hash
from shared.utils.config import Config


def _get_db_path(app_name):
    return Config.get_db_path(app_name)


def create_pre_account_social(email, display_name):
    social_db = _get_db_path("pawsteps")
    if not os.path.exists(social_db):
        return False

    try:
        conn = sqlite3.connect(social_db)
        cursor = conn.cursor()

        exists = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            conn.close()
            return True

        username = email.split("@")[0].replace(".", "").replace("_", "").replace(" ", "").lower()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            username += str(random.randint(100, 999))

        pwd_hash = generate_password_hash(secrets.token_urlsafe(32))

        cursor.execute(
            "INSERT INTO users (username, email, password_hash, display_name, status) VALUES (?, ?, ?, ?, ?)",
            (username, email, pwd_hash, display_name, "PENDENTE"),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[CROSS-DB ERROR] Failed to pre-create social account: {e}")
        return False


def sync_social_account(old_email, new_email, status=None, password_hash=None):
    social_db = _get_db_path("pawsteps")
    if not os.path.exists(social_db):
        return False
    try:
        conn = sqlite3.connect(social_db)
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

        if not updates:
            conn.close()
            return False

        params.append(old_email)
        query = f"UPDATE users SET {', '.join(updates)} WHERE email = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[CROSS-DB ERROR] Failed to sync social account: {e}")
        return False


def deactivate_account_everywhere(email):
    for app_name in ["cgrf", "pawsteps", "shop"]:
        try:
            db_path = _get_db_path(app_name)
            if not os.path.exists(db_path):
                continue
            conn = sqlite3.connect(db_path)
            if app_name == "cgrf":
                conn.execute("UPDATE usuarios_sistema SET status = 'INATIVO' WHERE email = ?", (email,))
            else:
                conn.execute("UPDATE users SET status = 'INATIVO' WHERE email = ?", (email,))
            conn.commit()
            conn.close()
        except Exception:
            pass


def check_email_conflicts(email):
    conflicts = []
    for app_name, label in [("pawsteps", "Rede Social (PawSteps)"), ("shop", "Loja FurryCore")]:
        try:
            db_path = _get_db_path(app_name)
            if not os.path.exists(db_path):
                continue
            conn = sqlite3.connect(db_path)
            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                conflicts.append(label)
            conn.close()
        except Exception:
            pass
    return conflicts
