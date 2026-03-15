import os
import sys
from flask import Flask, render_template, session, redirect, request, url_for

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core_i18n import configure_i18n

app = Flask(__name__)
# A sessão requer uma key
app.secret_key = 'landing-secret'
configure_i18n(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lang/<lang>')
def set_language(lang):
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(port=20000, debug=True)
