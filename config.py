import os
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

# ── Helper: build DB URI from individual params ──────────────
def _build_db_url():
    """
    Prefers the full DATABASE_URL env var.
    Falls back to assembling it from individual DB_* params.
    Supports both sqlite:/// and postgresql:// prefixes.
    """
    url = os.environ.get('DATABASE_URL')
    if url:
        # Handle Heroku-style 'postgres://' -> 'postgresql://'
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '5432')
    name = os.environ.get('DB_NAME', 'online_examination_system')
    user = os.environ.get('DB_USER', 'exam_admin')
    pwd  = os.environ.get('DB_PASSWORD', 'password')
    return f'postgresql://{user}:{pwd}@{host}:{port}/{name}'


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Base configuration shared across all environments."""

    # ── Flask Core ───────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345!')
    DEBUG   = False
    TESTING = False

    # ── SQLAlchemy ───────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI    = _build_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS  = {
        'pool_pre_ping': True,
        'pool_recycle':  300,
    }

    # ── CSRF Protection (Flask-WTF) ──────────────────────────
    WTF_CSRF_ENABLED   = True
    WTF_CSRF_TIME_LIMIT = 3600         # 1 hour

    # ── File Uploads ─────────────────────────────────────────
    UPLOAD_FOLDER       = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH  = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))

    # ── Logging ──────────────────────────────────────────────
    LOG_DIR = os.path.join(BASE_DIR, 'logs')

    # ── Flask-Mail ───────────────────────────────────────────
    MAIL_SERVER         = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = os.environ.get('MAIL_USE_TLS',  'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # ── Session ──────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour


class DevelopmentConfig(Config):
    """Development — debug on, SQLite fallback if no DB configured."""
    DEBUG = True


class ProductionConfig(Config):
    """Production — strict security flags."""
    DEBUG    = False
    TESTING  = False
    SESSION_COOKIE_SECURE    = True
    REMEMBER_COOKIE_SECURE   = True
    REMEMBER_COOKIE_HTTPONLY = True


class TestingConfig(Config):
    """Testing — in-memory SQLite."""
    TESTING  = True
    DEBUG    = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Map FLASK_ENV strings to config classes
config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
