from datetime import datetime
from database import db

class StudentAnswer(db.Model):
    """
    Model representing students' answers submitted for questions.
    """
    __tablename__ = 'student_answers'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False, index=True)
    selected_answer = db.Column(db.String(10), nullable=True)
    answer_status = db.Column(db.Boolean, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', back_populates='answers')
    exam = db.relationship('Exam', back_populates='student_answers')
    question = db.relationship('Question', back_populates='student_answers')

    def __repr__(self):
        return f"<StudentAnswer student={self.student_id} question={self.question_id}>"
