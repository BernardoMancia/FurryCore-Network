import os
import sys
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from database.db_shop import ShopDatabaseManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core_i18n import configure_i18n

load_dotenv()

app = Flask(__name__)
configure_i18n(app)
app.config['SECRET_KEY'] = os.getenv('SHOP_SECRET_KEY', 'shop-secret-456')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

csrf = CSRFProtect(app)
db = ShopDatabaseManager()

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    """Vitrine da Loja"""
    products = db.execute_query("SELECT * FROM products WHERE stock > 0", fetchall=True)
    return render_template('shop_index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetchone=True)
    if not product:
        flash("Produto não encontrado.", "error")
        return redirect(url_for('index'))
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    """Carrinho de Compras"""
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    product = db.execute_query("SELECT * FROM products WHERE id = ?", (product_id,), fetchone=True)
    
    if product:
        cart = session.get('cart', [])
        found = False
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] += 1
                found = True
                break
        if not found:
            cart.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': 1
            })
        session['cart'] = cart
        flash(f"{product['name']} adicionado ao carrinho!", "success")
    
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    """Finalização de Compra (Simulada)"""
    cart = session.get('cart', [])
    if not cart:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for('index'))
    
    # Limpa o carrinho após a "compra"
    session.pop('cart', None)
    return "<h1>Pedido Realizado com Sucesso!</h1><p>Em breve você receberá os detalhes no seu e-mail.</p><a href='/'>Voltar para a Loja</a>"

@app.route('/calculate_shipping', methods=['POST'])
def calculate_shipping():
    """Simulação de Frete (Integração futura com Correios)"""
    zip_code = request.form.get('zip_code')
    # Lógica de integração aqui
    return jsonify({
        'status': 'success',
        'cost': 15.90,
        'deadline': '5 dias úteis'
    })

@app.route('/lang/<lang>')
def set_language(lang):
    if lang in ['pt', 'en', 'es']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    # A loja roda em porta diferente para o Proxy Reverso
    app.run(port=20003, debug=True)
