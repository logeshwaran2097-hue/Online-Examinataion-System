import os
import sys
import base64
import random
from datetime import datetime, date, time, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from database import db, bcrypt
from models import (User, Admin, Exam, Question, Option, StudentAnswer, Result, 
                    Attendance, ExamMonitoring, Certificate, Notification, ActivityLog, Leaderboard, Analytics)
from utils.timer import is_exam_session_active, get_remaining_seconds
from utils.proctoring import save_proctoring_snapshot, update_proctoring_violation
from utils.auto_save import get_student_saved_answers_map
from utils.exam_submission import process_exam_submission

exam_bp = Blueprint('exam', __name__, url_prefix='/exam')

def log_audit_event(user_id, role, activity):
    """
    Helper to record audit trails.
    """
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
        print(f"Error writing audit log: {e}", file=sys.stderr)

@exam_bp.before_request
@login_required
def check_role_auth():
    """
    Secures blueprints routes.
    Paths starting with '/exam/admin/' require admin accounts.
    Other paths require student accounts.
    """
    if request.path.startswith('/exam/admin/'):
        if not isinstance(current_user, Admin):
            flash('Access denied. Administrator permissions required.', 'danger')
            return redirect(url_for('admin.login'))
    else:
        if not isinstance(current_user, User):
            flash('Access denied. Student authorization required.', 'danger')
            return redirect(url_for('auth.login'))

@exam_bp.route('/instructions/<int:exam_id>')
def instructions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Validation: Has student already attempted this?
    existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if existing_result:
        flash('You have already completed this examination.', 'warning')
        return redirect(url_for('student.exams'))
        
    return render_template('student/exam_instructions.html', exam=exam)

@exam_bp.route('/start/<int:exam_id>', methods=['POST'])
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # 1. Double check eligibility & previous attempts
    existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if existing_result:
        flash('Multiple attempts are strictly prohibited.', 'danger')
        return redirect(url_for('student.exams'))
        
    # 2. Check scheduled details (is it active today?)
    if exam.exam_date and exam.exam_date != date.today() and exam.status != 'ongoing':
        flash('This exam is not active at the current date/schedule.', 'danger')
        return redirect(url_for('student.exams'))
        
    # 3. Create or fetch Attendance check-in
    attendance = Attendance.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if not attendance:
        attendance = Attendance(
            student_id=current_user.id,
            exam_id=exam_id,
            login_time=datetime.utcnow(),
            attendance_status='present'
        )
        db.session.add(attendance)
        
        # Init monitoring
        monitor = ExamMonitoring(
            student_id=current_user.id,
            exam_id=exam_id,
            tab_switch_count=0,
            suspicious_activity='Initialized webcam checks.'
        )
        db.session.add(monitor)
        db.session.commit()
        
        log_audit_event(current_user.id, 'student', f"Launched proctored exam ID: {exam_id} ({exam.exam_title})")
        
    return redirect(url_for('exam.take_exam_view', exam_id=exam_id))

@exam_bp.route('/take/<int:exam_id>')
def take_exam_view(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if session is active. If time expired, auto-submit!
    if not is_exam_session_active(current_user.id, exam_id):
        # Auto-submit
        return redirect(url_for('exam.submit_exam_processing', exam_id=exam_id, auto=1))
        
    # Shuffle order & store in session
    order_key = f"exam_{exam_id}_order"
    if order_key not in session:
        all_questions = Question.query.filter_by(exam_id=exam_id).all()
        q_ids = [q.id for q in all_questions]
        random.shuffle(q_ids)
        session[order_key] = q_ids
        
    order = session[order_key]
    
    if not order:
        flash('This examination does not contain any questions yet.', 'warning')
        return redirect(url_for('student.exams'))
        
    # Current question index
    current_index = int(request.args.get('q', 0))
    if current_index < 0 or current_index >= len(order):
        current_index = 0
        
    question_id = order[current_index]
    question = Question.query.get(question_id)
    
    # Get previously saved answer
    saved_answer = StudentAnswer.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id,
        question_id=question_id
    ).first()
    
    selected_option = saved_answer.selected_answer if saved_answer else None
    
    # Get all saved answers map for palettes coloring
    saved_map = get_student_saved_answers_map(current_user.id, exam_id)
    
    # Get flagged questions list
    flag_key = f"exam_{exam_id}_flags"
    if flag_key not in session:
        session[flag_key] = []
    flags = session[flag_key]
    
    remaining_seconds = get_remaining_seconds(current_user.id, exam_id)
    
    return render_template(
        'student/take_exam.html',
        exam=exam,
        question=question,
        current_index=current_index,
        total_questions=len(order),
        selected_option=selected_option,
        time_left=remaining_seconds,
        saved_map=saved_map,
        flags=flags,
        question_ids=order
    )

@exam_bp.route('/save-answer', methods=['POST'])
def save_answer_api():
    exam_id = request.form.get('exam_id')
    question_id = request.form.get('question_id')
    selected_answer = request.form.get('selected_answer', '').strip()
    
    if not (exam_id and question_id):
        return jsonify({"success": False, "message": "Missing arguments."}), 400
        
    # Check if time expired
    if not is_exam_session_active(current_user.id, int(exam_id)):
        return jsonify({"success": False, "expired": True, "message": "Session expired."}), 403
        
    # Evaluate correctness status
    q = Question.query.get(question_id)
    is_correct = (selected_answer == q.correct_answer) if q else False
    
    ans = StudentAnswer.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id,
        question_id=question_id
    ).first()
    
    if not ans:
        ans = StudentAnswer(
            student_id=current_user.id,
            exam_id=exam_id,
            question_id=question_id,
            selected_answer=selected_answer,
            answer_status=is_correct
        )
        db.session.add(ans)
    else:
        ans.selected_answer = selected_answer
        ans.answer_status = is_correct
        ans.submitted_at = datetime.utcnow()
        
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@exam_bp.route('/toggle-flag', methods=['POST'])
def toggle_flag_api():
    exam_id = request.form.get('exam_id')
    question_id = int(request.form.get('question_id'))
    
    flag_key = f"exam_{exam_id}_flags"
    if flag_key not in session:
        session[flag_key] = []
        
    flags = session[flag_key]
    if question_id in flags:
        flags.remove(question_id)
        is_flagged = False
    else:
        flags.append(question_id)
        is_flagged = True
        
    session[flag_key] = flags
    session.modified = True
    return jsonify({"success": True, "flagged": is_flagged})

@exam_bp.route('/monitor/tab-switch', methods=['POST'])
def tab_switch_api():
    exam_id = int(request.form.get('exam_id'))
    
    monitor = update_proctoring_violation(current_user.id, exam_id, "Tab switched / window blur detected.")
    
    # Auto-submission limit (Warning 3)
    if monitor.tab_switch_count >= 3:
        # Trigger immediate submission
        return jsonify({"success": True, "switches": monitor.tab_switch_count, "auto_submit": True})
        
    return jsonify({"success": True, "switches": monitor.tab_switch_count, "auto_submit": False})

@exam_bp.route('/monitor/webcam', methods=['POST'])
def webcam_api():
    exam_id = int(request.form.get('exam_id'))
    image_base64 = request.form.get('image_data')
    
    if not image_base64:
        return jsonify({"success": False, "message": "Missing image snapshot."}), 400
        
    filepath = save_proctoring_snapshot(current_user.id, exam_id, image_base64)
    if filepath:
        # Update monitoring DB
        monitor = ExamMonitoring.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
        if monitor:
            monitor.captured_image = filepath
            monitor.webcam_status = True
            db.session.commit()
        return jsonify({"success": True, "path": filepath})
        
    return jsonify({"success": False, "message": "Failed to store image."}), 500

@exam_bp.route('/review-questions/<int:exam_id>')
def review_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    order_key = f"exam_{exam_id}_order"
    if order_key not in session:
        return redirect(url_for('exam.take_exam_view', exam_id=exam_id))
        
    order = session[order_key]
    questions_list = Question.query.filter(Question.id.in_(order)).all()
    
    # Map questions for fast ordered lookup
    q_map = {q.id: q for q in questions_list}
    ordered_questions = [q_map[qid] for qid in order if qid in q_map]
    
    saved_map = get_student_saved_answers_map(current_user.id, exam_id)
    
    flag_key = f"exam_{exam_id}_flags"
    flags = session.get(flag_key, [])
    
    # Calculate quick totals
    total = len(order)
    answered = len(saved_map)
    unanswered = total - answered
    flagged = len(flags)
    
    return render_template(
        'student/review_questions.html',
        exam=exam,
        questions=ordered_questions,
        saved_map=saved_map,
        flags=flags,
        total=total,
        answered=answered,
        unanswered=unanswered,
        flagged=flagged
    )

@exam_bp.route('/submit/<int:exam_id>', methods=['GET', 'POST'])
def submit_exam_processing(exam_id):
    """
    Bug #9 Fix: All scoring / certificate / notification logic delegated to
    utils.exam_submission.process_exam_submission — single source of truth.
    """
    exam = Exam.query.get_or_404(exam_id)
    is_auto = bool(request.args.get('auto', 0))

    # Guard against duplicate submissions
    existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if existing_result:
        return redirect(url_for('exam.exam_completed_view', exam_id=exam_id))

    # Clean session state
    session.pop(f"exam_{exam_id}_order", None)
    session.pop(f"exam_{exam_id}_flags", None)

    # Delegate to shared submission engine
    process_exam_submission(current_user.id, exam_id, exam, is_auto=is_auto)

    return redirect(url_for('exam.exam_completed_view', exam_id=exam_id))

@exam_bp.route('/completed/<int:exam_id>')
def exam_completed_view(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    result = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    return render_template('student/exam_completed.html', exam=exam, result=result)


# Admin Proctoring View Routing
@exam_bp.route('/admin/monitor')
def admin_monitor():
    """
    Lists active examination sessions and allows proctors to track tab-switches and webcam snapshots in real time.
    """
    # Active logins (attendance records without logout_time)
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

@exam_bp.route('/admin/force-submit/<int:attendance_id>', methods=['POST'])
def force_submit(attendance_id):
    """
    Allows administrator to force terminate an active student exam session.
    """
    sess = Attendance.query.get_or_404(attendance_id)
    student_id = sess.student_id
    exam_id = sess.exam_id
    
    # Complete the submission using student credentials context in DB
    sess.logout_time = datetime.utcnow()
    
    # Score calculation
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
    
    # Grade details
    if percentage >= 90: grade = 'A+'
    elif percentage >= 80: grade = 'A'
    elif percentage >= 70: grade = 'B'
    elif percentage >= 60: grade = 'C'
    elif percentage >= 50: grade = 'D'
    else: grade = 'F'
    
    pass_fail = 'pass' if obtained_marks >= sess.exam.pass_mark else 'fail'
    
    # Write Result
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
    
    # Write proctor activity violation log
    log_audit_event(student_id, 'student', f"Exam session terminated by administration proctor. (Score: {obtained_marks}/{total_marks})")
    
    # Alert notifications
    force_notif = Notification(
        user_id=student_id,
        title="Session Force Terminated",
        message=f"Your exam session for '{sess.exam.exam_title}' was force submitted by the administrator.",
        notification_type="system"
    )
    db.session.add(force_notif)
    db.session.commit()
    
    flash(f"Session for student {sess.student.full_name} has been force terminated and submitted.", 'success')
    return redirect(url_for('exam.admin_monitor'))
