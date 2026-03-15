import random
import string
import qrcode
import io
import base64
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

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

def gerar_qrcode_base64(cnf, domain="cgrf.com.br"):
    url = f"https://{domain}/perfil/{cnf}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def send_transactional_email(to_email, subject, html_content):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASS', '').strip()
    
    if not smtp_user or not smtp_password:
        return False

    msg = MIMEMultipart()
    msg['From'] = f"FurryCore Network <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

def send_welcome_email(user_data):
    if not user_data.get('email'):
        return False
    subject = "🔑 Ative sua Identidade Digital - FurryCore Network"
    login_url = "https://arwolf.com.br" # Dashboard centralizado
    html = f"""
    <div style="background-color: #0a0b10; color: #fff; padding: 40px; font-family: sans-serif; border: 1px solid #00f2ff; border-radius: 10px; max-width: 600px; margin: auto;">
        <h1 style="color: #00f2ff; text-align: center;">Seja Bem-vindo(a) à FurryCore!</h1>
        <p style="text-align: center;">Sua credencial <b>CGRF</b> foi emitida com sucesso.</p>
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #00f2ff;">
            <p><b>CNF:</b> {user_data['cnf']}</p>
            <p><b>RGF:</b> {user_data['rgf']}</p>
            <p style="color: #ffca2c;"><b>Senha Temporária:</b> {user_data.get('temp_pass', 'Verificar com Admin')}</p>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <a href="{login_url}" style="padding: 15px 30px; background: #00f2ff; color: #000; font-weight: bold; text-decoration: none; border-radius: 5px;">ACESSAR PAINEL</a>
        </div>
    </div>
    """
    return send_transactional_email(user_data['email'], subject, html)
