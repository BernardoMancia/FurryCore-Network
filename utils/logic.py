import random
import string
import qrcode
import io
import base64
from datetime import datetime

def gerar_cnf():
    parte1 = f"{random.randint(100, 999)}"
    parte2 = f"{random.randint(10, 99)}"
    parte3 = f"{random.randint(1000, 9999)}"
    dv = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"{parte1}.{parte2}.{parte3}-{dv}"

def gerar_rgf():
    parte1 = f"{random.randint(10, 99)}"
    parte2 = f"{random.randint(100, 999)}"
    parte3 = f"{random.randint(100, 999)}"
    dv = random.choice(string.ascii_uppercase)
    return f"{parte1}.{parte2}.{parte3}-{dv}"

def gerar_qrcode_base64(cnf, domain="82.112.245.99:6969"):
    url = f"http://{domain}/perfil/{cnf}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
