import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import config_map
from database import db, bcrypt, login_manager, mail
from routes import register_blueprints

csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Flask Application Factory.
    Selects config class based on FLASK_ENV environment variable.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    config_class = config_map.get(config_name, config_map['default'])

    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Create required directories ──────────────────────────
    for sub in ['', 'proctoring', 'profiles']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)

    # static/images and static/logo for the spec structure
    os.makedirs(os.path.join(app.root_path, 'static', 'images'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'logo'),   exist_ok=True)

    log_dir = app.config.get('LOG_DIR', os.path.join(app.root_path, 'logs'))
    os.makedirs(log_dir, exist_ok=True)

    # ── Logging setup ────────────────────────────────────────
    if not app.debug:
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'oes.log'),
            maxBytes=1_048_576,   # 1 MB per file
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Online Examination System startup')

    # ── Initialize Flask extensions ──────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # ── Register all Blueprints ──────────────────────────────
    register_blueprints(app)

    # ── Auto-create DB tables (SQLite dev mode) ──────────────
    with app.app_context():
        db.create_all()

    # ── Custom Error Handlers ────────────────────────────────
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        app.logger.error('Server Error: %s', error)
        return render_template('errors/500.html'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', True))
