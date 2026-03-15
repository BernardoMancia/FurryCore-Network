from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.db_social import SocialDatabaseManager

class SocialUser(UserMixin):
    def __init__(self, id, username, display_name, email, password_hash, cnf_vinculado=None, is_plus18=0, data_nascimento=None, status='ATIVO'):
        self.id = id
        self.username = username
        self.display_name = display_name
        self.email = email
        self.password_hash = password_hash
        self.cnf_vinculado = cnf_vinculado
        self.is_plus18 = is_plus18
        self.data_nascimento = data_nascimento
        self.status = status

    @staticmethod
    def get(user_id):
        db = SocialDatabaseManager()
        data = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetchone=True)
        if data:
            return SocialUser(data['id'], data['username'], data['display_name'], data['email'], data['password_hash'], data['cnf_vinculado'], data['is_plus18'], data['data_nascimento'], data['status'])
        return None

    @staticmethod
    def find_by_username(username):
        db = SocialDatabaseManager()
        data = db.execute_query("SELECT * FROM users WHERE username = ?", (username,), fetchone=True)
        if data:
            return SocialUser(data['id'], data['username'], data['display_name'], data['email'], data['password_hash'], data['cnf_vinculado'], data['is_plus18'], data['data_nascimento'], data['status'])
        return None

    @staticmethod
    def find_by_identifier(identifier):
        """Busca usuário por username ou e-mail."""
        db = SocialDatabaseManager()
        data = db.execute_query("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier), fetchone=True)
        if data:
            return SocialUser(data['id'], data['username'], data['display_name'], data['email'], data['password_hash'], data['cnf_vinculado'], data['is_plus18'], data['data_nascimento'], data['status'])
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
