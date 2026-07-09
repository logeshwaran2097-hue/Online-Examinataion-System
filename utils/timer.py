from datetime import datetime, timedelta
from models import Attendance, Exam

def is_exam_session_active(student_id, exam_id):
    """
    Validates on the server side if the student's exam attempt session is still active
    based on their recorded login timestamp and the exam duration constraints.
    Adds a grace period of 30 seconds for network latency.
    """
    attendance = Attendance.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if not attendance or not attendance.login_time:
        return False
        
    exam = Exam.query.get(exam_id)
    if not exam:
        return False
        
    allowed_duration = timedelta(minutes=exam.duration_minutes)
    grace_period = timedelta(seconds=30)
    
    elapsed = datetime.utcnow() - attendance.login_time
    if elapsed > (allowed_duration + grace_period):
        return False
        
    return True

def get_remaining_seconds(student_id, exam_id):
    """
    Returns remaining seconds for the student's active exam session.
    Returns 0 if time is fully expired.
    """
    attendance = Attendance.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if not attendance or not attendance.login_time:
        return 0
        
    exam = Exam.query.get(exam_id)
    if not exam:
        return 0
        
    total_seconds = exam.duration_minutes * 60
    elapsed_seconds = (datetime.utcnow() - attendance.login_time).total_seconds()
    
    remaining = int(total_seconds - elapsed_seconds)
    return max(0, remaining)
