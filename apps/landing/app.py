import os
import sys
from flask import Flask, render_template, session, redirect, request, url_for

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.utils.config import Config
from core_i18n import configure_i18n

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY_LANDING
configure_i18n(app)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/lang/<lang>")
def set_language(lang):
    if lang in ["pt", "en", "es"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 20000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
