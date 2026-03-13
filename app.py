import os
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from utils.security import sanitizar_input

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

csrf = CSRFProtect(app)
db = DatabaseManager()

@app.before_request
def monitor_session():
    session.permanent = True
    
    if request.method == 'POST':
        for key in request.form:
            request.form = request.form.copy()
            request.form[key] = sanitizar_input(request.form[key])

@app.route('/')
def index():
    return "CGRF 2.0 - Sistema de Governança de Identidades Furry"

@app.errorhandler(404)
def page_not_found(e):
    return "Erro 404 - Página não encontrada", 404

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 6969))
    app.run(host='0.0.0.0', port=port, debug=True)
