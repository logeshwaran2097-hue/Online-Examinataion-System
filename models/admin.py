from datetime import datetime
from database import db
from flask_login import UserMixin

class Admin(db.Model, UserMixin):
    """
    Model representing system administrators.
    """
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='admin')
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    exams_created = db.relationship('Exam', back_populates='creator')

    def get_id(self):
        return f"admin_{self.id}"

    def __repr__(self):
        return f"<Admin {self.username}>"
