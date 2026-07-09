from datetime import datetime
from database import db

class ExamMonitoring(db.Model):
    """
    Model representing anti-cheating tracking data for proctoring.
    """
    __tablename__ = 'exam_monitoring'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    tab_switch_count = db.Column(db.Integer, default=0)
    webcam_status = db.Column(db.Boolean, default=True)
    suspicious_activity = db.Column(db.Text, nullable=True)
    captured_image = db.Column(db.Text, nullable=True) # Paths to uploaded snapshots
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('tab_switch_count >= 0', name='chk_tab_switch'),
    )

    # Relationships
    student = db.relationship('User', back_populates='exam_monitors')
    exam = db.relationship('Exam', back_populates='exam_monitors')

    def __repr__(self):
        return f"<ExamMonitoring student={self.student_id} exam={self.exam_id} switches={self.tab_switch_count}>"
