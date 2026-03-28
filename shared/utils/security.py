import re
from functools import wraps
from markupsafe import escape
from flask import abort
from flask_login import current_user


def sanitizar_input(texto):
    if not isinstance(texto, str):
        return texto
    texto_limpo = re.sub(r"<script.*?>.*?</script>", "", texto, flags=re.DOTALL | re.IGNORECASE)
    texto_limpo = re.sub(r"<.*?>", "", texto_limpo)
    return escape(texto_limpo.strip())


def formatar_data_sp(dt_obj):
    import zoneinfo

    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    return dt_obj.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.cargo not in roles:
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_password_strength(password):
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Senha deve conter ao menos uma letra maiúscula."
    if not re.search(r"[a-z]", password):
        return False, "Senha deve conter ao menos uma letra minúscula."
    if not re.search(r"\d", password):
        return False, "Senha deve conter ao menos um número."
    return True, "OK"


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
