from flask import Flask
from .main import main_bp
from .auth import auth_bp
from .dashboard import dashboard_bp
from .admin import admin_bp
from .student import student_bp
from .exam import exam_bp
from .result import result_bp
from .analytics import analytics_bp
from .leaderboard import leaderboard_bp
from .monitoring import monitoring_bp

def register_blueprints(app: Flask):
    """
    Register application blueprints.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(monitoring_bp)

