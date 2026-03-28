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
    pawsteps_user = user_data.get("pawsteps_username", "")

    social_section = ""
    if pawsteps_user:
        social_section = f"""
        <div style="background: linear-gradient(135deg, rgba(0,229,255,0.08), rgba(168,85,247,0.08)); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid rgba(168,85,247,0.25);">
            <div style="text-align: center; margin-bottom: 12px;">
                <span style="font-size: 28px;">🌐</span>
            </div>
            <h3 style="color: #a855f7; margin: 0 0 8px 0; text-align: center; font-size: 16px;">Rede Social PawSteps</h3>
            <p style="text-align: center; margin: 0 0 6px 0; font-size: 14px; color: #ccc;">Sua conta social foi criada automaticamente!</p>
            <div style="text-align: center; margin: 16px 0;">
                <span style="display: inline-block; background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.3); padding: 10px 24px; border-radius: 20px; font-size: 18px; font-weight: bold; color: #00e5ff; letter-spacing: 0.5px;">@{pawsteps_user}</span>
            </div>
            <p style="text-align: center; margin: 8px 0 16px 0; font-size: 12px; color: #888;">Este é seu identificador na rede social. Após ativar sua conta, sua senha será sincronizada automaticamente.</p>
            <div style="text-align: center;">
                <a href="{social_url}/profile/{pawsteps_user}" style="display: inline-block; padding: 10px 28px; background: transparent; color: #a855f7; font-weight: bold; text-decoration: none; border-radius: 20px; border: 1px solid #a855f7; font-size: 13px;">VER MEU PERFIL NO PAWSTEPS</a>
            </div>
        </div>
        """

    vincular_section = ""
    if pawsteps_user:
        vincular_section = f"""
        <div style="margin-top: 20px; border: 1px dashed rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; text-align: center; background: rgba(255,255,255,0.02);">
            <p style="font-size: 13px; color: #999; margin: 0 0 8px 0;">Já possui uma conta diferente no PawSteps.social?</p>
            <a href="{social_url}/vincular?cnf={user_data['cnf']}&email={user_data['email']}" style="color: #00e5ff; text-decoration: underline; font-size: 13px;">Vincular CNF à conta existente</a>
        </div>
        """

    html = f"""
    <div style="background-color: #06070a; color: #ffffff; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: auto; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08);">

        <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); padding: 40px 32px 30px; text-align: center; border-bottom: 1px solid rgba(0,229,255,0.15);">
            <div style="font-size: 36px; margin-bottom: 12px;">🐾</div>
            <h1 style="color: #00e5ff; margin: 0 0 6px 0; font-size: 22px; font-weight: 700;">Bem-vindo(a) à FurryCore Network</h1>
            <p style="color: rgba(255,255,255,0.5); font-size: 14px; margin: 0;">Sua Identidade Digital CGRF foi emitida com sucesso.</p>
        </div>

        <div style="padding: 32px;">
            <div style="background: rgba(255,255,255,0.03); padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; border-left: 3px solid #00e5ff;">
                <h3 style="color: #00e5ff; margin: 0 0 14px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">📋 Suas Credenciais</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #888; width: 130px;">CNF</td>
                        <td style="padding: 6px 0; font-weight: bold;"><code style="background: #1a1b22; padding: 4px 10px; border-radius: 6px; font-size: 14px; color: #00e5ff;">{user_data['cnf']}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #888;">RGF</td>
                        <td style="padding: 6px 0; font-weight: bold; font-size: 14px;">{user_data['rgf']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #888;">Senha Temporária</td>
                        <td style="padding: 6px 0;"><code style="background: rgba(245,158,11,0.1); padding: 4px 10px; border-radius: 6px; font-size: 14px; color: #f59e0b; border: 1px solid rgba(245,158,11,0.2);">{user_data.get('temp_pass', 'Consultar Admin')}</code></td>
                    </tr>
                    {"<tr><td style='padding: 6px 0; font-size: 13px; color: #888;'>PawSteps</td><td style='padding: 6px 0; font-weight: bold; font-size: 14px; color: #a855f7;'>@" + pawsteps_user + "</td></tr>" if pawsteps_user else ""}
                </table>
                <p style="font-size: 11px; color: #666; margin: 14px 0 0 0;">* Altere sua senha imediatamente no primeiro acesso.</p>
            </div>

            {social_section}

            <div style="background: rgba(0,229,255,0.04); padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid rgba(0,229,255,0.1);">
                <h3 style="color: #00e5ff; margin: 0 0 14px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">🛡️ Ativação da Conta</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; vertical-align: top; width: 28px; font-size: 14px; color: #00e5ff; font-weight: bold;">1.</td>
                        <td style="padding: 8px 0; font-size: 13px; line-height: 1.5;">Acesse o portal CGRF com seu e-mail e a senha temporária acima.</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; vertical-align: top; font-size: 14px; color: #00e5ff; font-weight: bold;">2.</td>
                        <td style="padding: 8px 0; font-size: 13px; line-height: 1.5;">Crie uma nova senha forte e pessoal.</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; vertical-align: top; font-size: 14px; color: #00e5ff; font-weight: bold;">3.</td>
                        <td style="padding: 8px 0; font-size: 13px; line-height: 1.5;">Configure o MFA (Google Authenticator) para máxima segurança.</td>
                    </tr>
                </table>
            </div>

            <div style="text-align: center; margin: 32px 0 24px;">
                <a href="{portal_url}/login" style="display: inline-block; padding: 16px 48px; background: linear-gradient(135deg, #00e5ff, #a855f7); color: #000000; font-weight: 700; text-decoration: none; border-radius: 30px; text-transform: uppercase; letter-spacing: 1.5px; font-size: 14px; box-shadow: 0 4px 20px rgba(0,229,255,0.3);">ATIVAR MINHA CONTA</a>
            </div>

            {vincular_section}
        </div>

        <div style="padding: 20px 32px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.05); text-align: center;">
            <p style="font-size: 11px; color: #555; margin: 0;">FurryCore Network — Identidade Digital Segura para a Comunidade Furry</p>
            <p style="font-size: 10px; color: #444; margin: 6px 0 0 0;">
                <a href="https://cgrf.com.br" style="color: #555; text-decoration: none;">CGRF</a> ·
                <a href="https://pawsteps.social" style="color: #555; text-decoration: none;">PawSteps</a> ·
                <a href="https://furrycore.com.br/shop" style="color: #555; text-decoration: none;">Loja</a>
            </p>
        </div>
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
