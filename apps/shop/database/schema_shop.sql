-- CGRF Shop - Schema SQL
-- Loja Virtual para Venda de Carteiras Físicas

-- Tabela 1: products (Catálogo)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    weight_gr INTEGER NOT NULL, -- Gramas para frete
    length_cm INTEGER,
    width_cm INTEGER,
    height_cm INTEGER,
    image_url TEXT,
    stock INTEGER DEFAULT 0
);

-- Tabela 2: orders (Pedidos)
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    address_zip TEXT NOT NULL,
    address_street TEXT NOT NULL,
    address_number TEXT NOT NULL,
    address_city TEXT NOT NULL,
    address_state TEXT NOT NULL,
    total_products REAL NOT NULL,
    shipping_cost REAL NOT NULL,
    total_order REAL NOT NULL,
    payment_status TEXT DEFAULT 'PENDENTE', -- PENDENTE, PAGO, CANCELADO
    shipping_status TEXT DEFAULT 'PREPARANDO', -- PREPARANDO, ENVIADO, ENTREGUE
    tracking_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela 3: order_items (Detalhes do Pedido)
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price_at_purchase REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Inserindo produto base (Carteira CGRF)
INSERT INTO products (name, description, price, weight_gr, length_cm, width_cm, height_cm, stock)
VALUES ('Carteira CGRF Física', 'Identidade oficial Furry com impressão em PVC de alta qualidade e QR Code funcional.', 49.90, 50, 15, 10, 1, 999);
