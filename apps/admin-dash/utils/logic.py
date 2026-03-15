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
    smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('MAIL_PORT', 587))
    smtp_user = os.getenv('MAIL_USERNAME')
    # Pode vir como MAIL_PASSWORD ou SMTP_PASS em alguns ambientes
    # Remove espaços comuns em senhas de app do Google para evitar erros de copy-paste
    smtp_password = (os.getenv('MAIL_PASSWORD') or os.getenv('SMTP_PASS', '')).replace(" ", "").strip()
    
    if not smtp_user or not smtp_password:
        err = "Configurações de SMTP ausentes no arquivo .env"
        print(f"[SMTP ERROR] {err}")
        return False, err

    msg = MIMEMultipart()
    msg['From'] = f"FurryCore Network <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # SMTP_SSL se for porta 465
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
            
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ [SMTP SUCCESS] E-mail enviado para {to_email}")
        return True, "E-mail enviado com sucesso."
    except smtplib.SMTPAuthenticationError:
        err = "Falha de autenticação (Verifique a Senha de Aplicativo)."
        print(f"❌ [SMTP AUTH ERROR] {err}")
        return False, err
    except smtplib.SMTPConnectError:
        err = f"Falha ao conectar ao servidor {smtp_server}."
        print(f"❌ [SMTP CONN ERROR] {err}")
        return False, err
    except Exception as e:
        err = f"Erro inesperado: {str(e)}"
        print(f"❌ [SMTP EXCEPTION] {err}")
        return False, err

def create_pre_account_social(email, display_name):
    # O path do banco social é mapeado no docker-compose
    social_db = "/app/shared_data/pawsteps/pawsteps.db"
    if not os.path.exists(social_db):
        print(f"[SOCIAL ERROR] Banco de dados social não encontrado em {social_db}")
        return False
        
    try:
        conn = sqlite3.connect(social_db)
        # Verifica se o usuário já existe
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not exists:
            # Insere um usuário básico pendente de complementação de perfil
            # Ajustado para o esquema provável do PawSteps
            conn.execute("INSERT INTO users (username, email, password_hash, display_name, status) VALUES (?, ?, ?, ?, ?)",
                         (email.split('@')[0], email, 'EXTERNAL_AUTH_PENDING', display_name, 'INACTIVE'))
            conn.commit()
            print(f"[SOCIAL SUCCESS] Conta pré-criada para {email}")
        conn.close()
        return True
    except Exception as e:
        print(f"[SOCIAL ERROR] Falha ao criar conta social: {e}")
        return False

def send_welcome_email(user_data):
    if not user_data.get('email'):
        return False, "E-mail não fornecido."
    
    subject = "🐾 Ative sua Identidade Digital - FurryCore Network"
    portal_url = "https://cgrf.com.br"
    social_url = "https://pawsteps.social"
    
    html = f"""
    <div style="background-color: #0a0b10; color: #ffffff; padding: 40px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border: 1px solid #00f2ff; border-radius: 12px; max-width: 600px; margin: auto;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #00f2ff; margin-bottom: 5px;">Seja Bem-vindo(a)!</h1>
            <p style="color: #00f2ff; font-size: 1.1em; opacity: 0.8;">Sua Identidade Digital CGRF foi emitida.</p>
        </div>

        <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 8px; margin-bottom: 30px; border-left: 4px solid #00f2ff;">
            <h3 style="color: #00f2ff; margin-top: 0;">📋 Suas Credenciais</h3>
            <p style="margin: 10px 0;"><b>CNF:</b> <code style="background: #1a1b22; padding: 3px 6px; border-radius: 4px;">{user_data['cnf']}</code></p>
            <p style="margin: 10px 0;"><b>RGF:</b> {user_data['rgf']}</p>
            <p style="margin: 10px 0; color: #ffca2c;"><b>Senha Temporária:</b> <code style="background: #1a1b22; padding: 3px 6px; border-radius: 4px; color: #ffca2c;">{user_data.get('temp_pass', 'Verificar com Administrador')}</code></p>
            <p style="font-size: 0.85em; color: #aaa; margin-top: 15px;"><i>* Por segurança, altere sua senha imediatamente no primeiro acesso.</i></p>
        </div>

        <div style="margin-bottom: 30px;">
            <h3 style="color: #00f2ff;">🌐 Ecossistema FurryCore</h3>
            <p style="line-height: 1.6;">Sua conta é unificada em toda a nossa rede:</p>
            <ul style="line-height: 1.8;">
                <li><b>Portal CGRF:</b> Gerencie sua identidade e documentos.</li>
                <li><b>Rede Social PawSteps:</b> Sua conta já foi pré-criada! Basta acessar com o mesmo e-mail e sua nova senha após alterá-la.</li>
            </ul>
        </div>

        <div style="background: rgba(0, 242, 255, 0.05); padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px dashed #00f2ff;">
            <h3 style="color: #00f2ff; margin-top: 0;">🛡️ Segurança Extra (MFA)</h3>
            <p style="font-size: 0.9em; line-height: 1.5; margin-bottom: 0;">
                Recomendamos ativar o <b>MFA (Autenticação de Dois Fatores)</b> nas configurações do seu perfil no Portal CGRF para garantir a proteção máxima da sua identidade.
            </p>
        </div>

        <div style="text-align: center; margin-top: 40px;">
            <a href="{portal_url}" style="display: inline-block; padding: 16px 40px; background: #00f2ff; color: #000000; font-weight: bold; text-decoration: none; border-radius: 6px; text-transform: uppercase; letter-spacing: 1px;">ATIVAR MINHA CONTA</a>
        </div>
        
        <p style="text-align: center; font-size: 0.8em; color: #555; margin-top: 40px;">
            FurryCore Network - O Cofre de Identidades da Prowl.
        </p>
    </div>
    """
    return send_transactional_email(user_data['email'], subject, html)
