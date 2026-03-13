from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_manager import DatabaseManager

class User(UserMixin):
    def __init__(self, id, cnf_vinculado, email, cargo, senha_hash, totp_secret=None):
        self.id = id
        self.cnf_vinculado = cnf_vinculado
        self.email = email
        self.cargo = cargo
        self.senha_hash = senha_hash
        self.totp_secret = totp_secret

    @staticmethod
    def get(user_id):
        db = DatabaseManager()
        user_data = db.execute_query("SELECT * FROM usuarios_sistema WHERE id = ?", (user_id,), fetchone=True)
        if user_data:
            return User(user_data['id'], user_data['cnf_vinculado'], user_data['email'], user_data['cargo'], user_data['senha_hash'], user_data['totp_secret'])
        return None

    @staticmethod
    def find_by_email(email):
        db = DatabaseManager()
        user_data = db.execute_query("SELECT * FROM usuarios_sistema WHERE email = ?", (email,), fetchone=True)
        if user_data:
            return User(user_data['id'], user_data['cnf_vinculado'], user_data['email'], user_data['cargo'], user_data['senha_hash'], user_data['totp_secret'])
        return None

    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)
