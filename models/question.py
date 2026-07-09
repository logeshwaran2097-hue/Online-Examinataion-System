from datetime import datetime
from database import db

class Question(db.Model):
    """
    Model representing questions belonging to an exam.
    """
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(30), nullable=True)
    difficulty_level = db.Column(db.String(20), nullable=True)
    marks = db.Column(db.Integer, default=1)
    correct_answer = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('marks > 0', name='chk_question_marks'),
        db.CheckConstraint("question_type IN ('mcq', 'true_false', 'subjective')", name='chk_question_type'),
        db.CheckConstraint("difficulty_level IN ('easy', 'medium', 'hard')", name='chk_question_difficulty'),
    )

    # Relationships
    exam = db.relationship('Exam', back_populates='questions')
    options = db.relationship('Option', back_populates='question', uselist=False, cascade='all, delete-orphan')
    student_answers = db.relationship('StudentAnswer', back_populates='question', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Question id={self.id} type={self.question_type}>"


class Option(db.Model):
    """
    Model representing options for MCQ questions.
    """
    __tablename__ = 'options'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    option_a = db.Column(db.Text, nullable=True)
    option_b = db.Column(db.Text, nullable=True)
    option_c = db.Column(db.Text, nullable=True)
    option_d = db.Column(db.Text, nullable=True)

    # Relationships
    question = db.relationship('Question', back_populates='options')

    def __repr__(self):
        return f"<Option for Question id={self.question_id}>"



