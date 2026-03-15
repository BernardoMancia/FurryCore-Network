import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

def quick_test():
    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    smtp_user = "lukeolobosolitario@gmail.com"
    smtp_pass = os.getenv('SMTP_PASS', '').strip()
    
    print(f"Tentando login para {smtp_user} na porta {smtp_port}...")
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        server.login(smtp_user, smtp_pass)
        server.quit()
        print("CONEXÃO SMTP: SUCESSO!")
    except Exception as e:
        print(f"CONEXÃO SMTP: FALHA -> {e}")

if __name__ == "__main__":
    quick_test()
