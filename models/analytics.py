from datetime import datetime
from database import db




class Analytics(db.Model):
    """
    Model representing detailed historical performance analytics for students.
    """
    __tablename__ = 'analytics'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_name = db.Column(db.String(100), nullable=False)
    average_score = db.Column(db.Numeric(5, 2), default=0.00)
    exams_taken = db.Column(db.Integer, default=0)
    performance_level = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('average_score BETWEEN 0.00 AND 100.00', name='chk_avg_score'),
        db.CheckConstraint('exams_taken >= 0', name='chk_exams_taken'),
    )

    # Relationships
    student = db.relationship('User', back_populates='analytics_records')

    def __repr__(self):
        return f"<Analytics student={self.student_id} subject={self.subject_name} avg={self.average_score}>"
