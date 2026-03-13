import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from flask import current_app, render_template

def send_transactional_email(to_email, subject, html_content):
    """
    Envia e-mail transacional usando SMTP configurado no .env
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASS')
    
    if not smtp_user or not smtp_password:
        print("CRITICAL: SMTP configurado incorretamente. Verifique .env")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"CGRF 2.0 <{smtp_user}>"
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
    except Exception as e:
        print(f"ERRO AO ENVIAR E-MAIL: {e}")
        return False

def send_welcome_email(user_data):
    """
    Envia o e-mail de boas-vindas com instruções de MFA
    """
    if not user_data.get('email'):
        return False
        
    subject = "📜 Registro Confirmado - CGRF 2.0 / Portal de Identidade"
    
    # Gerar link de MFA (exemplo: rota de perfil que pede login)
    login_url = "http://127.0.0.1:6969/login"
    
    html = f"""
    <div style="background-color: #0a0b10; color: #fff; padding: 40px; font-family: sans-serif; border: 1px solid #00f2ff; border-radius: 10px;">
        <h1 style="color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);">Saudações, {user_data['nome']}!</h1>
        <p style="font-size: 16px;">Seu registro no <b>CGRF 2.0</b> foi emitido e confirmado com sucesso.</p>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; margin: 25px 0;">
            <p><b>CNF Gerado:</b> {user_data['cnf']}</p>
            <p><b>RGF:</b> {user_data['rgf']}</p>
        </div>

        <h3 style="color: #00f2ff;">🔒 Instruções de Segurança (MFA)</h3>
        <p>Para sua proteção total sob as normas de Governança Digital, recomendamos ativar a Autenticação de Dois Fatores (MFA):</p>
        <ol>
            <li>Acesse o portal via link abaixo.</li>
            <li>Faça login com sua conta administrativa ou pessoal.</li>
            <li>No seu perfil, escaneie o código QR de segurança.</li>
        </ol>

        <a href="{login_url}" style="display: inline-block; padding: 12px 25px; background-color: transparent; border: 1px solid #00f2ff; color: #00f2ff; text-decoration: none; border-radius: 5px; margin-top: 20px;">ACESSAR MEU PORTAL</a>
        
        <p style="margin-top: 40px; color: #666; font-size: 12px;">Este é um e-mail automático. Não responda.</p>
    </div>
    """
    
    return send_transactional_email(user_data['email'], subject, html)
