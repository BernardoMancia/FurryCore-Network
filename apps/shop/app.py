import os
import sys
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from shared.utils.config import Config
from core_i18n import configure_i18n
from database.db_shop import ShopDatabaseManager

load_dotenv()

app = Flask(__name__, static_url_path="/shop/static")
configure_i18n(app)
app.config["SECRET_KEY"] = Config.SECRET_KEY_SHOP
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

csrf = CSRFProtect(app)
db = ShopDatabaseManager()


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/")
def index():
    products = db.execute_query("SELECT * FROM products WHERE stock > 0", fetchall=True)
    cart_count = sum(item["quantity"] for item in session.get("cart", []))
    return render_template("shop_index.html", products=products, cart_count=cart_count)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetchone=True)
    if not product:
        flash("Produto não encontrado.", "error")
        return redirect(url_for("index"))
    cart_count = sum(item["quantity"] for item in session.get("cart", []))
    return render_template("product_detail.html", product=product, cart_count=cart_count)


@app.route("/cart")
def cart():
    cart_items = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    cart_count = sum(item["quantity"] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total, cart_count=cart_count)


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_id = int(request.form.get("product_id"))
    product = db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetchone=True)

    if product:
        cart = session.get("cart", [])
        found = False
        for item in cart:
            if item["id"] == product_id:
                item["quantity"] += 1
                found = True
                break
        if not found:
            cart.append(
                {"id": product["id"], "name": product["name"], "price": product["price"], "quantity": 1}
            )
        session["cart"] = cart
        flash(f"{product['name']} adicionado ao carrinho!", "success")

    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    cart_items = session.get("cart", [])
    if not cart_items:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("index"))

    total = sum(item["price"] * item["quantity"] for item in cart_items)
    session.pop("cart", None)
    return render_template("checkout_success.html", total=total)


@app.route("/calculate_shipping", methods=["POST"])
def calculate_shipping():
    zip_code = request.form.get("zip_code")
    return jsonify({"status": "success", "cost": 15.90, "deadline": "5 dias úteis"})


@app.route("/lang/<lang>")
def set_language(lang):
    if lang in ["pt", "en", "es"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 20003))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)
