import os
import sys
import base64
from datetime import datetime, date, time, timedelta
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session, jsonify
from flask_login import login_required, current_user
from database import db, bcrypt
from models import (User, Exam, Question, Option, StudentAnswer, Result, 
                    Attendance, ExamMonitoring, Certificate, Notification, ActivityLog, Leaderboard, Analytics)
from utils.charts import (get_student_academic_summary, get_student_progress_chart, 
                          get_subject_performance, analyze_weak_strong_subjects, predict_next_score_ai)
from utils.certificate_generator import generate_unique_certificate_number, generate_certificate_pdf
from utils.exam_submission import process_exam_submission

student_bp = Blueprint('student', __name__, url_prefix='/student')

def log_activity(activity):
    """
    Log a student audit event.
    """
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        log_entry = ActivityLog(
            user_id=user_id,
            user_role='student',
            activity=activity,
            ip_address=request.remote_addr or 'unknown',
            browser=request.user_agent.string[:255] or 'unknown'
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging student activity: {e}", file=sys.stderr)

@student_bp.before_request
def check_student_auth():
    """
    Restricts access to student module routes to authenticated student accounts only.
    Exempts public certificate verification from auth check.
    """
    if request.endpoint == 'student.verify_certificate':
        return
        
    if not current_user.is_authenticated:
        flash('Please authenticate to access the student panel.', 'danger')
        return redirect(url_for('auth.login'))
        
    if not isinstance(current_user, User):
        flash('Access denied. Please login with a student account.', 'danger')
        return redirect(url_for('auth.login'))

@student_bp.route('/dashboard')
def dashboard():
    # 1. Gather stats
    stats = get_student_academic_summary(current_user.id)
    
    # 2. Get available/upcoming exams
    # We list exams matching ongoing or upcoming, ordered by date
    available_exams = Exam.query.filter(Exam.status.in_(['ongoing', 'upcoming'])).order_by(Exam.exam_date, Exam.start_time).limit(5).all()
    
    # Check if student completed each exam
    completed_exam_ids = [r.exam_id for r in Result.query.filter_by(student_id=current_user.id).all()]
    
    # 3. Get recent results
    recent_results = Result.query.filter_by(student_id=current_user.id).order_by(Result.generated_at.desc()).limit(5).all()
    
    # 4. Unread notifications
    unread_notifs = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(4).all()
    
    # 5. Leaderboard position
    leaderboard_rank = Leaderboard.query.filter_by(student_id=current_user.id).first()
    
    # 6. Trend data (Chart.js)
    trend_data = get_student_progress_chart(current_user.id)
    
    return render_template(
        'student/dashboard.html',
        stats=stats,
        available_exams=available_exams,
        completed_exam_ids=completed_exam_ids,
        recent_results=recent_results,
        unread_notifs=unread_notifs,
        leaderboard_rank=leaderboard_rank,
        trend_data=trend_data
    )

@student_bp.route('/profile')
def profile():
    return render_template('student/profile.html', student=current_user)

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not full_name:
            flash('Full Name is required.', 'danger')
            return render_template('student/edit_profile.html', student=current_user)
            
        # Duplicate Phone check
        if phone_number and phone_number != current_user.phone_number:
            dup_phone = User.query.filter_by(phone_number=phone_number).first()
            if dup_phone:
                flash('This phone number is already registered by another account.', 'danger')
                return render_template('student/edit_profile.html', student=current_user)
                
        current_user.full_name = full_name
        current_user.phone_number = phone_number if phone_number else None
        
        # Password update
        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('student/edit_profile.html', student=current_user)
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            log_activity('Changed password')
            
        try:
            db.session.commit()
            log_activity('Updated profile details')
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving profile changes: {e}", 'danger')
            
    return render_template('student/edit_profile.html', student=current_user)

@student_bp.route('/profile/avatar', methods=['POST'])
def upload_avatar():
    file = request.files.get('profile_image')
    if not file:
        flash('No file provided.', 'danger')
        return redirect(url_for('student.profile'))
        
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        flash('Invalid image format. Allowed formats: PNG, JPG, JPEG, GIF.', 'danger')
        return redirect(url_for('student.profile'))
        
    try:
        # Encapsulate image as Base64 in DB for zero-dependency local filesystem persistence
        img_bytes = file.read()
        encoded = base64.b64encode(img_bytes).decode('utf-8')
        current_user.profile_image = f"data:{file.mimetype};base64,{encoded}"
        db.session.commit()
        log_activity('Uploaded profile avatar')
        flash('Profile image updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error uploading image: {e}", 'danger')
        
    return redirect(url_for('student.profile'))

@student_bp.route('/exams')
def exams():
    search_query = request.args.get('search', '').strip()
    subject_filter = request.args.get('subject', '').strip()
    
    # Base query for ongoing or upcoming exams
    query = Exam.query.filter(Exam.status.in_(['ongoing', 'upcoming']))
    
    if search_query:
        query = query.filter(Exam.exam_title.ilike(f"%{search_query}%"))
    if subject_filter:
        query = query.filter(Exam.subject_name.ilike(f"%{subject_filter}%"))
        
    exams_list = query.order_by(Exam.exam_date.asc(), Exam.start_time.asc()).all()
    
    # Get subjects list for filters
    subjects = db.session.query(Exam.subject_name).distinct().all()
    subjects = [s[0] for s in subjects if s[0]]
    
    # Check if student completed each exam
    completed_exam_ids = [r.exam_id for r in Result.query.filter_by(student_id=current_user.id).all()]
    
    return render_template(
        'student/exams.html',
        exams=exams_list,
        subjects=subjects,
        completed_exam_ids=completed_exam_ids,
        search_query=search_query,
        subject_filter=subject_filter
    )

@student_bp.route('/exam/<int:exam_id>/instructions')
def exam_instructions(exam_id):
    """
    Bug #8 Fix: Redirect to the canonical exam blueprint instructions route
    to avoid duplicate route logic. The exam blueprint owns the instructions page.
    """
    return redirect(url_for('exam.instructions', exam_id=exam_id))

@student_bp.route('/exam/<int:exam_id>/take')
def take_exam(exam_id):
    exam = Exam.query.get(exam_id)
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('student.exams'))
        
    # Prevent multiple attempts
    existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if existing_result:
        flash('You have already attempted this exam.', 'warning')
        return redirect(url_for('student.exams'))
        
    # Set attendance records
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
            tab_switch_count=0
        )
        db.session.add(monitor)
        db.session.commit()
        
    # Prepare question order and store in session (Random shuffle)
    q_session_key = f"exam_{exam_id}_q_order"
    if q_session_key not in session:
        all_q_ids = [q.id for q in Question.query.filter_by(exam_id=exam_id).all()]
        random.shuffle(all_q_ids)
        session[q_session_key] = all_q_ids
        
    q_order = session[q_session_key]
    
    if not q_order:
        flash('This exam contains no questions.', 'warning')
        return redirect(url_for('student.exams'))
        
    # Get current question index (default to 0)
    current_index = int(request.args.get('q', 0))
    if current_index < 0 or current_index >= len(q_order):
        current_index = 0
        
    current_question_id = q_order[current_index]
    question = Question.query.get(current_question_id)
    
    # Get user's saved answer for this question
    saved_answer = StudentAnswer.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id,
        question_id=current_question_id
    ).first()
    
    selected_option = saved_answer.selected_answer if saved_answer else None
    
    # Calculate time left
    time_limit_seconds = exam.duration_minutes * 60
    time_spent = (datetime.utcnow() - attendance.login_time).total_seconds()
    time_left = max(0, int(time_limit_seconds - time_spent))
    
    # Get answers counts for the palette grid
    all_answers = StudentAnswer.query.filter_by(student_id=current_user.id, exam_id=exam_id).all()
    answered_q_ids = [ans.question_id for ans in all_answers if ans.selected_answer]
    
    # Flags dict
    flag_key = f"exam_{exam_id}_flags"
    if flag_key not in session:
        session[flag_key] = []
        
    flagged_ids = session[flag_key]
    
    return render_template(
        'student/take_exam.html',
        exam=exam,
        question=question,
        current_index=current_index,
        total_questions=len(q_order),
        selected_option=selected_option,
        time_left=time_left,
        answered_q_ids=answered_q_ids,
        flagged_ids=flagged_ids,
        question_ids=q_order
    )

@student_bp.route('/exam/<int:exam_id>/save-answer', methods=['POST'])
def save_answer(exam_id):
    """
    AJAX endpoint to auto-save selected options.
    """
    question_id = request.form.get('question_id')
    selected_answer = request.form.get('selected_answer')
    
    if not question_id:
        return jsonify({"success": False, "message": "Missing question ID"}), 400
        
    # Check if answer exists
    ans = StudentAnswer.query.filter_by(
        student_id=current_user.id,
        exam_id=exam_id,
        question_id=question_id
    ).first()
    
    # Fetch correct answer to evaluate status
    q = Question.query.get(question_id)
    is_correct = (selected_answer == q.correct_answer) if q else False
    
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
        
    try:
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

@student_bp.route('/exam/<int:exam_id>/toggle-flag', methods=['POST'])
def toggle_flag(exam_id):
    """
    Toggle Mark for Review state of a question.
    """
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

@student_bp.route('/exam/<int:exam_id>/submit', methods=['POST'])
def submit_exam(exam_id):
    """
    Bug #9 Fix: All scoring / certificate / notification logic is now delegated
    to utils.exam_submission.process_exam_submission so it lives in ONE place.
    """
    exam = Exam.query.get(exam_id)
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('student.exams'))

    # Prevent duplicate results
    existing_res = Result.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if existing_res:
        flash('You have already submitted this exam.', 'warning')
        return redirect(url_for('student.exams'))

    # Clean session state first
    session.pop(f"exam_{exam_id}_q_order", None)
    session.pop(f"exam_{exam_id}_flags", None)

    # Delegate to shared submission engine
    res = process_exam_submission(current_user.id, exam_id, exam, is_auto=False)

    flash(f"Exam '{exam.exam_title}' submitted successfully!", 'success')
    return redirect(url_for('student.review_exam', exam_id=exam_id, result_id=res.id))

@student_bp.route('/exam/<int:exam_id>/review/<int:result_id>')
def review_exam(exam_id, result_id):
    exam = Exam.query.get(exam_id)
    result = Result.query.get(result_id)
    
    if not (exam and result) or result.student_id != current_user.id:
        flash('Results transcript not found.', 'danger')
        return redirect(url_for('student.exams'))
        
    # Get questions with options
    questions = Question.query.filter_by(exam_id=exam_id).order_by(Question.id).all()
    user_answers = StudentAnswer.query.filter_by(student_id=current_user.id, exam_id=exam_id).all()
    answers_map = {ans.question_id: ans for ans in user_answers}
    
    return render_template(
        'student/review_exam.html',
        exam=exam,
        result=result,
        questions=questions,
        answers_map=answers_map
    )

@student_bp.route('/results')
def results():
    res_list = Result.query.filter_by(student_id=current_user.id).order_by(Result.generated_at.desc()).all()
    return render_template('student/results.html', results=res_list)

@student_bp.route('/analytics')
def analytics():
    return redirect(url_for('analytics_bp.index'))

@student_bp.route('/leaderboard')
def leaderboard():
    # Global rankings
    global_board = Leaderboard.query.order_by(Leaderboard.rank_position.asc()).limit(20).all()
    
    # Department rankings
    dept_board = db.session.query(Leaderboard).join(User, User.id == Leaderboard.student_id)\
     .filter(User.department == current_user.department)\
     .order_by(Leaderboard.rank_position.asc()).limit(20).all()
     
    # Find current user rank
    my_rank = Leaderboard.query.filter_by(student_id=current_user.id).first()
    
    return render_template(
        'student/leaderboard.html',
        global_board=global_board,
        dept_board=dept_board,
        my_rank=my_rank
    )

@student_bp.route('/certificates')
def certificates():
    certs = Certificate.query.filter_by(student_id=current_user.id).order_by(Certificate.generated_date.desc()).all()
    return render_template('student/certificates.html', certificates=certs)

@student_bp.route('/certificate/<int:cert_id>/download')
def download_certificate(cert_id):
    cert = Certificate.query.get(cert_id)
    if not cert or cert.student_id != current_user.id:
        flash('Certificate not found.', 'danger')
        return redirect(url_for('student.certificates'))
        
    try:
        # Generate PDF certificate
        issue_date_str = cert.generated_date.strftime('%B %d, %Y')
        host_url = request.host_url.rstrip('/')
        verif_url = f"{host_url}/student/verify-certificate/{cert.certificate_number}"
        
        pdf_buf = generate_certificate_pdf(
            student_name=current_user.full_name,
            exam_title=cert.exam.exam_title,
            score=int(float(Result.query.filter_by(student_id=current_user.id, exam_id=cert.exam_id).first().percentage)),
            certificate_number=cert.certificate_number,
            issue_date_str=issue_date_str,
            verification_url=verif_url
        )
        
        # Download log
        log_activity(f"Downloaded certificate PDF serial: {cert.certificate_number}")
        
        return send_file(
            pdf_buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Certificate_{cert.certificate_number}.pdf"
        )
    except Exception as e:
        flash(f"Error compiling certificate PDF: {e}", 'danger')
        return redirect(url_for('student.certificates'))

@student_bp.route('/verify-certificate/<string:cert_no>')
def verify_certificate(cert_no):
    """
    Public verification endpoint to validate a certificate.
    Exempted from student authentication wrapper.
    """
    cert = Certificate.query.filter_by(certificate_number=cert_no).first()
    if not cert:
        return render_template('student/verify_certificate.html', cert=None, cert_no=cert_no)
        
    result = Result.query.filter_by(student_id=cert.student_id, exam_id=cert.exam_id).first()
    return render_template('student/verify_certificate.html', cert=cert, result=result, cert_no=cert_no)

@student_bp.route('/notifications')
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('student/notifications.html', notifications=notifs)

@student_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Notification not found"}), 404

@student_bp.route('/notifications/read-all', methods=['POST'])
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({Notification.is_read: True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('student.notifications'))

@student_bp.route('/history')
def history():
    logs = ActivityLog.query.filter_by(user_id=current_user.id, user_role='student').order_by(ActivityLog.created_at.desc()).all()
    return render_template('student/history.html', logs=logs)

@student_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('student.settings'))
    return render_template('student/settings.html')

@student_bp.route('/monitor/tab-switch', methods=['POST'])
def tab_switch():
    """
    Log proctor tab switches for anti-cheating audit.
    """
    exam_id = request.form.get('exam_id')
    if not exam_id:
        return jsonify({"success": False, "message": "Missing exam ID"}), 400
        
    monitor = ExamMonitoring.query.filter_by(student_id=current_user.id, exam_id=exam_id).first()
    if monitor:
        monitor.tab_switch_count += 1
        monitor.suspicious_activity = f"Focus lost / Tab switched {monitor.tab_switch_count} times."
        db.session.commit()
        
        # Log to system audits
        log_activity(f"Anti-Cheating Trigger: Tab switch detected during exam ID: {exam_id}. Total count: {monitor.tab_switch_count}")
        return jsonify({"success": True, "switches": monitor.tab_switch_count})
        
    return jsonify({"success": False, "message": "Monitoring record not found"}), 404
