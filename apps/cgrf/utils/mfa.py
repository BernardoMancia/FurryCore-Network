import pyotp
import qrcode
import io
import base64

def gerar_segredo_totp():
    return pyotp.random_base32()

def gerar_qr_totp(email, secret, issuer="CGRF 2.0"):
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)
    qr = qrcode.make(uri)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def validar_totp(secret, token):
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
