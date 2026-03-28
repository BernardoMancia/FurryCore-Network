import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from shared.utils.config import Config


def send_transactional_email(to_email, subject, html_content):
    smtp_server = Config.SMTP_SERVER
    smtp_port = Config.SMTP_PORT
    smtp_user = Config.SMTP_USER
    smtp_password = Config.SMTP_PASS

    if not smtp_user or not smtp_password:
        err = "SMTP credentials missing in .env"
        print(f"[SMTP ERROR] {err}")
        return False, err

    msg = MIMEMultipart()
    msg["From"] = f"FurryCore Network <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()

        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"[SMTP SUCCESS] E-mail sent to {to_email}")
        return True, "E-mail enviado com sucesso."
    except smtplib.SMTPAuthenticationError:
        err = "Authentication failed (check App Password)."
        print(f"[SMTP AUTH ERROR] {err}")
        return False, err
    except smtplib.SMTPConnectError:
        err = f"Connection failed to {smtp_server}."
        print(f"[SMTP CONN ERROR] {err}")
        return False, err
    except Exception as e:
        err = f"Unexpected error: {str(e)}"
        print(f"[SMTP EXCEPTION] {err}")
        return False, err


def send_welcome_email(user_data):
    if not user_data.get("email"):
        return False, "E-mail not provided."

    subject = "🐾 Ative sua Identidade Digital - FurryCore Network"
    portal_url = Config.get_portal_url("cgrf")
    social_url = Config.get_portal_url("pawsteps")

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

        <div style="margin-top: 30px; border: 1px dashed #555; padding: 20px; border-radius: 8px; text-align: center;">
            <h4 style="color: #00f2ff; margin-top: 0;">🌐 Já possui uma conta no PawSteps.social?</h4>
            <p style="font-size: 14px;">Utilize o link abaixo para vincular sua nova CNF diretamente à sua conta social existente:</p>
            <a href="{social_url}/vincular?cnf={user_data['cnf']}&email={user_data['email']}" style="color: #00f2ff; text-decoration: underline; font-size: 14px;">Vincular à conta social existente</a>
        </div>

        <p style="text-align: center; font-size: 0.8em; color: #555; margin-top: 40px;">
            FurryCore Network - O Cofre de Identidades da Prowl.
        </p>
    </div>
    """
    return send_transactional_email(user_data["email"], subject, html)


def send_privacy_status_email(to_email, nome, status, tipo_acao, motivo=""):
    if status == "APROVADO":
        color = "#00f2ff"
        status_text = "APROVADA"
        icon = "✅"
        msg_header = "Sua privacidade é nossa prioridade."
    else:
        color = "#ffca2c"
        status_text = "RECUSADA"
        icon = "⚠️"
        msg_header = "Sua solicitação precisa de ajustes."

    subject = f"{icon} Status da Solicitação de Privacidade - CGRF 2.0"

    if tipo_acao == "REMOVER":
        detalhe_tipo = "Exclusão Total de Dados (Direito de Esquecimento)"
        msg_acao = (
            "Seu registro foi completamente removido de nossa base de dados pública e privada."
            if status == "APROVADO"
            else "Sua solicitação de exclusão total foi revisada."
        )
    else:
        detalhe_tipo = "Alteração/Ocultação Parcial de Dados"
        msg_acao = (
            "As alterações solicitadas foram aplicadas e seu perfil foi atualizado."
            if status == "APROVADO"
            else "Analisamos seu pedido de alteração de dados."
        )

    motivo_block = ""
    if status == "REJEITADO" and motivo:
        motivo_block = f"""
        <div style="background: rgba(255,100,100,0.1); padding: 15px; border-radius: 5px; border: 1px dashed #ff4444; margin-top: 15px;">
            <p style="margin: 0; color: #ff6666;"><b>Motivo da Recusa:</b></p>
            <p style="margin: 10px 0 0 0; color: #eee;">{motivo}</p>
        </div>
        """

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
            {motivo_block}
        </div>

        <p style="margin-top: 30px; border-top: 1px solid #333; padding-top: 20px; font-size: 14px; color: #888;">
            Este é um comunicado automático de conformidade com a <b>LGPD (Lei Geral de Proteção de Dados)</b>.
            Se você tiver dúvidas sobre este processo, entre em contato com o suporte administrativo.
        </p>

        <p style="margin-top: 20px; color: #555; font-size: 11px; text-align: center;">🛡️ FurryCore Network - Governança Segura e Identidade Digital Furry.</p>
    </div>
    """
    return send_transactional_email(to_email, subject, html)
