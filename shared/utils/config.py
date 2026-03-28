import os
import secrets


class Config:
    CGRF_DOMAIN = os.getenv("CGRF_DOMAIN", "cgrf.com.br")
    PAWSTEPS_DOMAIN = os.getenv("PAWSTEPS_DOMAIN", "pawsteps.social")
    SHOP_DOMAIN = os.getenv("SHOP_DOMAIN", "furrycore.com.br")
    LANDING_DOMAIN = os.getenv("LANDING_DOMAIN", "furrycore.com.br")
    ADMIN_DOMAIN = os.getenv("ADMIN_DOMAIN", "arwolf.com.br")
    VPS_IP = "82.112.245.99"

    SECRET_KEY_LANDING = os.getenv("SECRET_KEY_LANDING", secrets.token_urlsafe(64))
    SECRET_KEY_CGRF = os.getenv("SECRET_KEY_CGRF", secrets.token_urlsafe(64))
    SECRET_KEY_PAWSTEPS = os.getenv("SECRET_KEY_PAWSTEPS", secrets.token_urlsafe(64))
    SECRET_KEY_SHOP = os.getenv("SECRET_KEY_SHOP", secrets.token_urlsafe(64))
    SECRET_KEY_ADMIN = os.getenv("SECRET_KEY_ADMIN", secrets.token_urlsafe(64))

    SMTP_SERVER = os.getenv("SMTP_SERVER", os.getenv("MAIL_SERVER", "smtp.gmail.com"))
    SMTP_PORT = int(os.getenv("SMTP_PORT", os.getenv("MAIL_PORT", 587)))
    SMTP_USER = os.getenv("SMTP_USER", os.getenv("MAIL_USERNAME", ""))
    SMTP_PASS = os.getenv("SMTP_PASS", os.getenv("MAIL_PASSWORD", "")).replace(" ", "").strip()

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")

    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
    ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm"}

    DB_PATHS = {
        "cgrf": os.getenv("CGRF_DB_PATH", "/app/shared_data/cgrf/base_cgrf.db"),
        "pawsteps": os.getenv("PAWSTEPS_DB_PATH", "/app/shared_data/pawsteps/pawsteps.db"),
        "shop": os.getenv("SHOP_DB_PATH", "/app/shared_data/shop/shop.db"),
    }

    @classmethod
    def get_portal_url(cls, app_name="cgrf"):
        domains = {
            "cgrf": f"https://{cls.CGRF_DOMAIN}",
            "pawsteps": f"https://{cls.PAWSTEPS_DOMAIN}",
            "shop": f"https://{cls.SHOP_DOMAIN}/shop",
            "landing": f"https://{cls.LANDING_DOMAIN}",
            "admin": f"https://{cls.ADMIN_DOMAIN}",
        }
        return domains.get(app_name, f"https://{cls.CGRF_DOMAIN}")

    @classmethod
    def get_db_path(cls, app_name):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        fallbacks = {
            "cgrf": os.path.join(base_dir, "apps", "cgrf", "database", "base_cgrf.db"),
            "pawsteps": os.path.join(base_dir, "apps", "pawsteps", "database", "pawsteps.db"),
            "shop": os.path.join(base_dir, "apps", "shop", "database", "shop.db"),
        }
        docker_path = cls.DB_PATHS.get(app_name, "")
        if os.path.exists(docker_path):
            return docker_path
        return fallbacks.get(app_name, docker_path)
