from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models import Admin, Attendance, ExamMonitoring, Question, StudentAnswer, Result, ActivityLog, Notification

monitoring_bp = Blueprint('monitoring_bp', __name__, url_prefix='/monitoring')

def log_audit_event(user_id, role, activity):
    try:
        log_entry = ActivityLog(
            user_id=user_id,
            user_role=role,
            activity=activity,
            ip_address=request.remote_addr or 'unknown',
            browser=request.user_agent.string[:255] or 'unknown'
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

@monitoring_bp.before_request
@login_required
def check_role_auth():
    if not isinstance(current_user, Admin):
        flash('Access denied. Administrator authorization required.', 'danger')
        return redirect(url_for('admin.login'))

@monitoring_bp.route('/')
def index():
    """
    Renders live active students grid.
    """
    active_sessions = Attendance.query.filter(Attendance.logout_time.is_(None))\
     .order_by(Attendance.login_time.desc()).all()
     
    session_data = []
    for sess in active_sessions:
        monitor = ExamMonitoring.query.filter_by(student_id=sess.student_id, exam_id=sess.exam_id).first()
        session_data.append({
            "attendance_id": sess.id,
            "student_name": sess.student.full_name,
            "student_email": sess.student.email,
            "exam_title": sess.exam.exam_title,
            "login_time": sess.login_time.strftime('%H:%M:%S') if sess.login_time else '--',
            "tab_switches": monitor.tab_switch_count if monitor else 0,
            "webcam_image": monitor.captured_image if monitor else None,
            "suspicious_log": monitor.suspicious_activity if monitor else 'No logs.'
        })
        
    return render_template('admin/exam_monitor.html', sessions=session_data)

@monitoring_bp.route('/force-submit/<int:attendance_id>', methods=['POST'])
def force_submit(attendance_id):
    """
    Terminates active exams sessions.
    """
    sess = Attendance.query.get_or_404(attendance_id)
    student_id = sess.student_id
    exam_id = sess.exam_id
    
    sess.logout_time = datetime.utcnow()
    
    questions = Question.query.filter_by(exam_id=exam_id).all()
    total_marks = sum(q.marks for q in questions)
    obtained_marks = 0
    
    user_answers = StudentAnswer.query.filter_by(student_id=student_id, exam_id=exam_id).all()
    answers_map = {ans.question_id: ans.selected_answer for ans in user_answers}
    
    for q in questions:
        sel = answers_map.get(q.id)
        if sel == q.correct_answer:
            obtained_marks += q.marks
            
    percentage = (obtained_marks / total_marks * 100.0) if total_marks > 0 else 0.0
    
    if percentage >= 90: grade = 'A+'
    elif percentage >= 80: grade = 'A'
    elif percentage >= 70: grade = 'B'
    elif percentage >= 60: grade = 'C'
    elif percentage >= 50: grade = 'D'
    else: grade = 'F'
    
    pass_fail = 'pass' if obtained_marks >= sess.exam.pass_mark else 'fail'
    
    res = Result(
        student_id=student_id,
        exam_id=exam_id,
        total_marks=total_marks,
        obtained_marks=obtained_marks,
        percentage=percentage,
        grade=grade,
        pass_fail_status=pass_fail
    )
    db.session.add(res)
    db.session.commit()
    
    log_audit_event(student_id, 'student', f"Attempt force-terminated by proctor monitor dashboard.")
    
    force_notif = Notification(
        user_id=student_id,
        title="Exam Terminated by Admin",
        message=f"Your active exam session for '{sess.exam.exam_title}' was force submitted by the admin proctor monitor.",
        notification_type="system"
    )
    db.session.add(force_notif)
    db.session.commit()
    
    flash(f"Exam attempt for student {sess.student.full_name} has been force closed.", 'success')
    return redirect(url_for('monitoring_bp.index'))
