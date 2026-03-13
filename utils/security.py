import re
from markupsafe import escape

def sanitizar_input(texto):
    if not isinstance(texto, str):
        return texto
    
    texto_limpo = re.sub(r'<script.*?>.*?</script>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    texto_limpo = re.sub(r'<.*?>', '', texto_limpo)
    
    return escape(texto_limpo.strip())

def formatar_data_sp(dt_obj):
    import zoneinfo
    tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    return dt_obj.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")
