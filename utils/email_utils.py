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
    smtp_password = os.getenv('SMTP_PASS', '').strip()
    
    if not smtp_user or not smtp_password:
        print("CRITICAL: SMTP configurado incorretamente. Verifique .env")
        return False

    msg = MIMEMultipart()
    msg['From'] = f"CGRF 2.0 <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        print(f"[DEBUG] Conectando ao servidor SMTP: {smtp_server}:{smtp_port}", flush=True)
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.set_debuglevel(1)
        print(f"[DEBUG] Autenticando usuário: {smtp_user}", flush=True)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"[SUCCESS] E-mail enviado com sucesso para {to_email}", flush=True)
        return True
    except Exception as e:
        print(f"[CRITICAL ERROR] Falha ao enviar e-mail para {to_email}: {e}", flush=True)
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

def send_privacy_status_email(to_email, nome, status, tipo_acao, motivo=""):
    """
    Envia e-mail estilizado sobre o status da solicitação LGPD
    """
    if status == 'APROVADO':
        color = "#00f2ff" # Cyan
        status_text = "APROVADA"
        icon = "✅"
        msg_header = "Sua privacidade é nossa prioridade."
    else:
        color = "#ffca2c" # Gold/Yellow
        status_text = "RECUSADA"
        icon = "⚠️"
        msg_header = "Sua solicitação precisa de ajustes."

    subject = f"{icon} Status da Solicitação de Privacidade - CGRF 2.0"
    
    # Detalhes específicos por tipo
    if tipo_acao == 'REMOVER':
        detalhe_tipo = "Exclusão Total de Dados (Direito de Esquecimento)"
        msg_acao = "Seu registro foi completamente removido de nossa base de dados pública e privada." if status == 'APROVADO' else "Sua solicitação de exclusão total foi revisada."
    else:
        detalhe_tipo = "Alteração/Ocultação Parcial de Dados"
        msg_acao = "As alterações solicitadas foram aplicadas e seu perfil foi atualizado." if status == 'APROVADO' else "Analisamos seu pedido de alteração de dados."

    html = f"""
    <div style="background-color: #0a0b10; color: #fff; padding: 40px; font-family: sans-serif; border: 1px solid {color}; border-radius: 10px; max-width: 600px; margin: auto;">
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 40px;">{icon}</span>
        </div>
        <h1 style="color: {color}; text-align: center; text-shadow: 0 0 10px {color}80; margin-top: 0;">Solicitação {status_text}</h1>
        <p style="font-size: 16px; text-align: center; color: #aaa;">{msg_header}</p>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {color};">
            <p style="margin: 5px 0;"><b>Titular:</b> {nome}</p>
            <p style="margin: 5px 0;"><b>Tipo de Ação:</b> {detalhe_tipo}</p>
            <p style="margin: 5px 0;"><b>Status Final:</b> <span style="color: {color}; font-weight: bold;">{status_text}</span></p>
        </div>

        <div style="padding: 10px 0;">
            <p style="line-height: 1.6;">{msg_acao}</p>
            
            {f'''<div style="background: rgba(255,100,100,0.1); padding: 15px; border-radius: 5px; border: 1px dashed #ff4444; margin-top: 15px;">
                <p style="margin: 0; color: #ff6666;"><b>Motivo da Recusa:</b></p>
                <p style="margin: 10px 0 0 0; color: #eee;">{motivo}</p>
            </div>''' if status == 'REJEITADO' and motivo else ''}
        </div>

        <p style="margin-top: 30px; border-top: 1px solid #333; padding-top: 20px; font-size: 14px; color: #888;">
            Este é um comunicado automático de conformidade com a <b>LGPD (Lei Geral de Proteção de Dados)</b>.
            Se você tiver dúvidas sobre este processo, entre em contato com o suporte administrativo.
        </p>
        
        <p style="margin-top: 20px; color: #555; font-size: 11px; text-align: center;">🛡️ CGRF 2.0 - Governança Segura e Identidade Digital Furry.</p>
    </div>
    """
    
    return send_transactional_email(to_email, subject, html)
