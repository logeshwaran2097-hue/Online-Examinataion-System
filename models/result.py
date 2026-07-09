from datetime import datetime
from database import db

class Result(db.Model):
    """
    Model representing finalized exam results.
    """
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    total_marks = db.Column(db.Integer, nullable=True)
    obtained_marks = db.Column(db.Integer, nullable=True)
    percentage = db.Column(db.Numeric(5, 2), nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    pass_fail_status = db.Column(db.String(10), nullable=True)
    rank = db.Column(db.Integer, nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('obtained_marks >= 0 AND obtained_marks <= total_marks', name='chk_result_marks'),
        db.CheckConstraint('percentage BETWEEN 0.00 AND 100.00', name='chk_result_percentage'),
        db.CheckConstraint("pass_fail_status IN ('pass', 'fail')", name='chk_result_pass_status'),
    )

    # Relationships
    student = db.relationship('User', back_populates='results')
    exam = db.relationship('Exam', back_populates='results')

    def __repr__(self):
        return f"<Result student={self.student_id} exam={self.exam_id} score={self.obtained_marks}>"



class Notification(db.Model):
    """
    Model representing notifications for students.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=True)
    notification_type = db.Column(db.String(50), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id} read={self.is_read}>"


class ActivityLog(db.Model):
    """
    Model representing system audit logs.
    """
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    user_role = db.Column(db.String(20), nullable=True)
    activity = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    browser = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog user={self.user_id} activity={self.activity[:20]}>"
