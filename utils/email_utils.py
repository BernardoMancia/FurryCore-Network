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
    Envia o e-mail de boas-vindas com instruções detalhadas de ativação
    """
    if not user_data.get('email'):
        return False
        
    subject = "🔑 Ative sua Identidade Digital - CGRF 2.0"
    
    login_url = "http://127.0.0.1:6969/login" # Ajustar para IP da VPS no deploy final
    
    html = f"""
    <div style="background-color: #0a0b10; color: #fff; padding: 40px; font-family: sans-serif; border: 1px solid #00f2ff; border-radius: 10px; max-width: 600px; margin: auto;">
        <h1 style="color: #00f2ff; text-align: center; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5);">Seja Bem-vindo(a), {user_data['nome']}!</h1>
        <p style="font-size: 16px; text-align: center;">Sua credencial oficial <b>CGRF 2.0</b> foi emitida e sua conta de acesso foi criada.</p>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #00f2ff;">
            <p style="margin: 5px 0;"><b>CNF:</b> {user_data['cnf']}</p>
            <p style="margin: 5px 0;"><b>RGF:</b> {user_data['rgf']}</p>
            <p style="margin: 5px 0; color: #ffca2c;"><b>Senha Temporária:</b> <code style="background: #222; padding: 2px 5px;">{user_data.get('temp_pass', 'Verificar com Admin')}</code></p>
        </div>

        <h3 style="color: #00f2ff; border-bottom: 1px solid #333; padding-bottom: 10px;">🛡️ Guia de Ativação Obrigatória</h3>
        <p>Para ativar sua identidade e garantir sua segurança, siga exatamente estes passos:</p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; vertical-align: top;"><b style="color: #00f2ff;">1. PRIMEIRA SENHA:</b></td>
                <td style="padding: 10px 0;">Acesse o portal e use seu e-mail e a senha temporária acima.</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; vertical-align: top;"><b style="color: #00f2ff;">2. RESET DE SENHA:</b></td>
                <td style="padding: 10px 0;">O sistema solicitará imediatamente que você crie uma nova senha forte e pessoal.</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; vertical-align: top;"><b style="color: #00f2ff;">3. ATIVAÇÃO MFA:</b></td>
                <td style="padding: 10px 0;">Após trocar a senha, você será levado para a tela de Segurança. Escaneie o código QR com o Google Authenticator ou similar.</td>
            </tr>
        </table>

        <div style="text-align: center; margin-top: 30px;">
            <a href="{login_url}" style="display: inline-block; padding: 15px 30px; background: #00f2ff; color: #000; font-weight: bold; text-decoration: none; border-radius: 5px; box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);">ATIVAR MINHA CONTA AGORA</a>
        </div>
        
        <p style="margin-top: 40px; color: #888; font-size: 12px; text-align: center;">🛡️ CGRF 2.0 - Governança e Transparência Furry. <br> Este link expira em 24h.</p>
    </div>
    """
    
    return send_transactional_email(user_data['email'], subject, html)
