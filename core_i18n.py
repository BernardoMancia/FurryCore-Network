from flask import session

# Dicionário Multilíngue Simples (i18n)
TRANSLATIONS = {
    'pt': {
        'lang_name': 'Português',
        # Navbar Global
        'nav_home': 'Início',
        'nav_portal': 'Portal CGRF',
        'nav_social': 'PawSteps',
        'nav_shop': 'Loja',
        'nav_login': 'Login',
        'nav_logout': 'Sair',
        'nav_logout': 'Sair',
        'nav_profile': 'Meu Perfil',
        'nav_wallet': 'Minha Carteira',
        'nav_records': 'Registros',
        'nav_users': 'Usuários',
        'nav_privacy': 'Privacidade',
        'nav_explore': 'Explorar',
        'nav_map': 'Mapa de Amigos',
        'nav_messages': 'Mensagens',
        'btn_post': 'Postar',
        
        # Página de Login/Cadastro
        'login_title': 'Acesso ao Ecossistema',
        'login_btn': 'Entrar',
        'register_title': 'Crie sua Conta Social',
        'register_btn': 'Criar Minha Conta',
        'lbl_username': 'Username',
        'lbl_display_name': 'Nome de Exibição',
        'lbl_email': 'E-mail',
        'lbl_password': 'Senha',
        'lbl_confirm_password': 'Confirmar Senha',
        'lbl_age': 'Sua Idade',
        'lbl_dob': 'Data de Nascimento',
        'terms_check': 'Li e aceito os',
        'terms_link': 'Termos de Uso e Serviço da FurryCore Network',
        
        # Avisos Formulario
        'pass_mismatch': 'As senhas não coincidem.',
        'age_warning': 'Somente maiores de 18 podem habilitar conteúdo NSFW futuramente.',
        'nsfw_wish': 'Desejo ter a opção de ver conteúdo **NSFW** (+18)',
        
        # Landing Page
        'landing_subtitle': 'Sua porta de entrada para o mundo Furry digital.',
        'landing_cgrf_desc': 'Consulte identidades, verifique perfis e explore o registro oficial da comunidade.',
        'landing_cgrf_btn': 'Consultar Registros',
        'landing_social_desc': 'Conecte-se, compartilhe momentos e participe dos maiores eventos da comunidade.',
        'landing_social_btn': 'Abrir Rede Social',
        'landing_shop_desc': 'Produtos oficiais, carteiras físicas premium e colecionáveis exclusivos.',
        'landing_shop_btn': 'Visitar Loja',
        'footer_rights': '© 2026 FurryCore Network. Todos os direitos reservados no ecossistema.'
    },
    'en': {
        'lang_name': 'English',
        # Navbar Global
        'nav_home': 'Home',
        'nav_portal': 'CGRF Portal',
        'nav_social': 'PawSteps',
        'nav_shop': 'Shop',
        'nav_login': 'Login',
        'nav_logout': 'Logout',
        'nav_logout': 'Logout',
        'nav_profile': 'My Profile',
        'nav_wallet': 'My Wallet',
        'nav_records': 'Records',
        'nav_users': 'Users',
        'nav_privacy': 'Privacy',
        'nav_explore': 'Explore',
        'nav_map': 'Friend Map',
        'nav_messages': 'Messages',
        'btn_post': 'Post',
        
        # Página de Login/Cadastro
        'login_title': 'Ecosystem Access',
        'login_btn': 'Sign In',
        'register_title': 'Create your Social Account',
        'register_btn': 'Create My Account',
        'lbl_username': 'Username',
        'lbl_display_name': 'Display Name',
        'lbl_email': 'Email',
        'lbl_password': 'Password',
        'lbl_confirm_password': 'Confirm Password',
        'lbl_age': 'Your Age',
        'lbl_dob': 'Date of Birth',
        'terms_check': 'I read and agree to the',
        'terms_link': 'Terms of Use and Service of FurryCore Network',
        
        # Avisos Formulario
        'pass_mismatch': 'Passwords do not match.',
        'age_warning': 'Only users over 18 can enable NSFW content later.',
        'nsfw_wish': 'I wish to have the option to see **NSFW** content (+18)',
        
        # Landing Page
        'landing_subtitle': 'Your gateway to the digital Furry world.',
        'landing_cgrf_desc': 'Check identities, verify profiles, and explore the official community registry.',
        'landing_cgrf_btn': 'Consult Records',
        'landing_social_desc': 'Connect, share moments, and participate in the biggest community events.',
        'landing_social_btn': 'Open Social Network',
        'landing_shop_desc': 'Official products, premium physical id-cards, and exclusive collectibles.',
        'landing_shop_btn': 'Visit Shop',
        'footer_rights': '© 2026 FurryCore Network. All rights reserved across the ecosystem.'
    },
    'es': {
        'lang_name': 'Español',
        # Navbar Global
        'nav_home': 'Inicio',
        'nav_portal': 'Portal CGRF',
        'nav_social': 'PawSteps',
        'nav_shop': 'Tienda',
        'nav_login': 'Iniciar Sesión',
        'nav_logout': 'Cerrar Sesión',
        'nav_logout': 'Cerrar Sesión',
        'nav_profile': 'Mi Perfil',
        'nav_wallet': 'Mi Billetera',
        'nav_records': 'Registros',
        'nav_users': 'Usuarios',
        'nav_privacy': 'Privacidad',
        'nav_explore': 'Explorar',
        'nav_map': 'Mapa de Amigos',
        'nav_messages': 'Mensajes',
        'btn_post': 'Publicar',
        
        # Página de Login/Cadastro
        'login_title': 'Acceso al Ecosistema',
        'login_btn': 'Ingresar',
        'register_title': 'Crea tu Cuenta Social',
        'register_btn': 'Crear Mi Cuenta',
        'lbl_username': 'Usuario',
        'lbl_display_name': 'Nombre de Visualización',
        'lbl_email': 'Correo',
        'lbl_password': 'Contraseña',
        'lbl_confirm_password': 'Confirmar Contraseña',
        'lbl_age': 'Tu Edad',
        'lbl_dob': 'Fecha de Nacimiento',
        'terms_check': 'He leído y acepto los',
        'terms_link': 'Términos de Uso y Servicio de FurryCore Network',
        
        # Avisos Formulario
        'pass_mismatch': 'Las contraseñas no coinciden.',
        'age_warning': 'Solo los mayores de 18 años pueden habilitar contenido NSFW en el futuro.',
        'nsfw_wish': 'Deseo tener la opción de ver contenido **NSFW** (+18)',
        
        # Landing Page
        'landing_subtitle': 'Tu puerta de entrada al mundo Furry digital.',
        'landing_cgrf_desc': 'Consulta identidades, verifica perfiles y explora el registro oficial de la comunidad.',
        'landing_cgrf_btn': 'Consultar Registros',
        'landing_social_desc': 'Conéctate, comparte momentos y participa en los mayores eventos de la comunidad.',
        'landing_social_btn': 'Abrir Red Social',
        'landing_shop_desc': 'Productos oficiales, tarjetas físicas premium y coleccionables exclusivos.',
        'landing_shop_btn': 'Visitar Tienda',
        'footer_rights': '© 2026 FurryCore Network. Todos los derechos reservados en el ecosistema.'
    }
}

def get_locale():
    # Retorna o idioma salvo na sessão ou o padrão "pt"
    return session.get('lang', 'pt')

def t(key):
    # Função tradutora chamada dentro do Jinja
    lang = get_locale()
    return TRANSLATIONS.get(lang, TRANSLATIONS['pt']).get(key, key)

def configure_i18n(app):
    # Registra a função de tradução (t) globalmente para todos os templates Jinja do App
    @app.context_processor
    def inject_t():
        return dict(t=t, current_lang=get_locale())
