from datetime import datetime
from database import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """
    Model representing students/users of the system.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.Integer, nullable=True)
    profile_image = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Brute-force protection fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint('year_of_study BETWEEN 1 AND 8', name='chk_year_of_study'),
    )

    # Relationships
    answers = db.relationship('StudentAnswer', back_populates='student', cascade='all, delete-orphan')
    results = db.relationship('Result', back_populates='student', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', back_populates='student', cascade='all, delete-orphan')
    exam_monitors = db.relationship('ExamMonitoring', back_populates='student', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', back_populates='student', cascade='all, delete-orphan')
    leaderboard_entry = db.relationship('Leaderboard', back_populates='student', uselist=False, cascade='all, delete-orphan')
    analytics_records = db.relationship('Analytics', back_populates='student', cascade='all, delete-orphan')

    def get_id(self):
        return f"user_{self.id}"

    def __repr__(self):
        return f"<User {self.email}>"
