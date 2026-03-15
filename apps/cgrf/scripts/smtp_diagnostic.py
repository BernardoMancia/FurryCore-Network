import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def diagnostic():
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    print(f"--- DIAGNÓSTICO SMTP ---")
    print(f"Servidor: {smtp_server}:{smtp_port}")
    print(f"Usuário: {smtp_user}")
    print(f"Senha (tamanho): {len(smtp_pass) if smtp_pass else 0}")
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = smtp_user
    msg['Subject'] = "Teste de Diagnóstico CGRF 2.0"
    msg.attach(MIMEText("Teste de envio.", 'plain'))

    try:
        print(f"\n[1] Conectando ao servidor ({smtp_server}:{smtp_port})...", flush=True)
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            print("\n[2] Iniciando TLS...", flush=True)
            server.starttls()
            
        server.set_debuglevel(1)
        
        print("\n[3] Tentando Login...", flush=True)
        server.login(smtp_user, smtp_pass)
        
        print("\n[4] Enviando Mensagem...", flush=True)
        server.send_message(msg)
        
        print("\n[5] Encerrando...", flush=True)
        server.quit()
        print("\nRESULTADO: SUCESSO ABSOLUTO.")
    except Exception as e:
        print(f"\nRESULTADO: FALHA CRÍTICA -> {e}")

if __name__ == "__main__":
    diagnostic()
