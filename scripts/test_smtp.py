import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = os.getenv('SMTP_USER')
smtp_pass = os.getenv('SMTP_PASS')

print(f"Testando SMTP para: {smtp_user}")
# Tentar remover espaços se falhar
smtp_pass_clean = smtp_pass.replace(" ", "")

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.set_debuglevel(1)
    server.starttls()
    print("Iniciando login...")
    server.login(smtp_user, smtp_pass)
    print("Login com espaços: SUCESSO")
    server.quit()
except Exception as e:
    print(f"Login com espaços: FALHOU ({e})")
    try:
        print("Tentando sem espaços...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass_clean)
        print("Login sem espaços: SUCESSO")
        server.quit()
    except Exception as e2:
        print(f"Login sem espaços: FALHOU ({e2})")
