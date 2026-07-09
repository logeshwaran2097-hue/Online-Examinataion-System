from datetime import datetime
from database import db

class Certificate(db.Model):
    """
    Model representing completion certificates generated for student exams.
    """
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    certificate_number = db.Column(db.String(100), unique=True, nullable=False)
    qr_code = db.Column(db.Text, nullable=True)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', back_populates='certificates')
    exam = db.relationship('Exam', back_populates='certificates')

    def __repr__(self):
        return f"<Certificate {self.certificate_number} student={self.student_id}>"
