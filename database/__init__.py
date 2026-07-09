from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

# Instantiate Flask extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

# Set up basic LoginManager configuration
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(session_id):
    if not session_id:
        return None
    session_id = str(session_id)
    if session_id.startswith("admin_"):
        from models import Admin
        try:
            return Admin.query.get(int(session_id.split("_")[1]))
        except (ValueError, IndexError):
            return None
    elif session_id.startswith("user_"):
        from models import User
        try:
            return User.query.get(int(session_id.split("_")[1]))
        except (ValueError, IndexError):
            return None
    else:
        # Fallback for old/unprefixed user IDs
        from models import User
        try:
            return User.query.get(int(session_id))
        except ValueError:
            return None

