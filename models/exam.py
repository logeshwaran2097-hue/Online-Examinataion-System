from datetime import datetime
from database import db

class Exam(db.Model):
    """
    Model representing examinations.
    """
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    exam_title = db.Column(db.String(150), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer, default=0)
    pass_mark = db.Column(db.Integer, default=0)
    exam_date = db.Column(db.Date, nullable=True, index=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(20), default='upcoming', index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('duration_minutes > 0', name='chk_exam_duration'),
        db.CheckConstraint('total_questions >= 0', name='chk_exam_questions'),
        db.CheckConstraint('total_marks >= 0', name='chk_exam_total_marks'),
        db.CheckConstraint('pass_mark >= 0 AND pass_mark <= total_marks', name='chk_exam_pass_mark'),
        db.CheckConstraint("status IN ('upcoming', 'ongoing', 'completed', 'cancelled')", name='chk_exam_status'),
    )

    # Relationships
    creator = db.relationship('Admin', back_populates='exams_created')
    questions = db.relationship('Question', back_populates='exam', cascade='all, delete-orphan')
    results = db.relationship('Result', back_populates='exam', cascade='all, delete-orphan')
    student_answers = db.relationship('StudentAnswer', back_populates='exam', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', back_populates='exam', cascade='all, delete-orphan')
    exam_monitors = db.relationship('ExamMonitoring', back_populates='exam', cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', back_populates='exam', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Exam {self.exam_title}>"


class Attendance(db.Model):
    """
    Model representing student attendance for exams.
    """
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False, index=True)
    login_time = db.Column(db.DateTime, nullable=True)
    logout_time = db.Column(db.DateTime, nullable=True)
    attendance_status = db.Column(db.String(20), nullable=True)

    __table_args__ = (
        db.CheckConstraint("attendance_status IN ('present', 'absent', 'late', 'suspended')", name='chk_attendance_status'),
        db.CheckConstraint("logout_time IS NULL OR logout_time >= login_time", name='chk_attendance_logout'),
    )

    # Relationships
    student = db.relationship('User', back_populates='attendance_records')
    exam = db.relationship('Exam', back_populates='attendance_records')

    def __repr__(self):
        return f"<Attendance student={self.student_id} exam={self.exam_id} status={self.attendance_status}>"



