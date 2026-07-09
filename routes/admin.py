import csv
from datetime import datetime, date, time
from io import StringIO, BytesIO
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from database import db, bcrypt
from models import User, Admin, Exam, Question, Option, StudentAnswer, Result, Attendance, ExamMonitoring, Certificate, Notification, ActivityLog, Leaderboard, Analytics
from utils.analytics import get_performance_data, get_subject_analysis, get_pass_fail_statistics, get_exam_participation, get_monthly_activity, get_leaderboard_rankings
from utils.pdf_generator import generate_certificate_pdf, generate_results_pdf
from utils.qr_generator import generate_qr_code_base64
import openpyxl

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def log_admin_activity(activity):
    """
    Log an administrative audit event.
    """
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        log_entry = ActivityLog(
            user_id=user_id,
            user_role='admin',
            activity=activity,
            ip_address=request.remote_addr or 'unknown',
            browser=request.user_agent.string[:255] or 'unknown'
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging admin activity: {e}")

def seed_default_admin():
    """
    Ensures at least one administrator account exists in the database.
    """
    try:
        if not Admin.query.first():
            hashed_pw = bcrypt.generate_password_hash('adminpassword').decode('utf-8')
            default_admin = Admin(
                username='admin',
                email='admin@eduexam.com',
                password=hashed_pw,
                role='admin'
            )
            db.session.add(default_admin)
            db.session.commit()
            print("INFO: Seeded default administrator account (admin / adminpassword)")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding default admin: {e}")

@admin_bp.before_request
def check_admin_auth():
    # Make sure we have at least one admin seeded
    seed_default_admin()
    
    # Exempt admin login from RBAC check
    if request.endpoint == 'admin.login':
        return
        
    if not current_user.is_authenticated or not isinstance(current_user, Admin):
        flash('Access denied. Please authenticate as administrator.', 'danger')
        return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')

        if not (username and password):
            flash('Please enter your credentials.', 'danger')
            return render_template('admin/login.html')

        admin = Admin.query.filter_by(username=username).first()

        if admin and bcrypt.check_password_hash(admin.password, password):
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log in admin using flask-login
            login_user(admin)
            log_admin_activity('Admin logged in')
            
            flash('Admin authentication successful.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            return render_template('admin/login.html')

    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    log_admin_activity('Admin logged out')
    logout_user()
    session.clear()
    flash('Logged out from admin panel.', 'success')
    return redirect(url_for('admin.login'))


# --- Dashboard Home ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Calculate stats
    total_students = User.query.count()
    total_admins = Admin.query.count()
    total_exams = Exam.query.count()
    total_questions = Question.query.count()
    active_exams = Exam.query.filter_by(status='ongoing').count()
    completed_exams = Exam.query.filter_by(status='completed').count()
    total_results = Result.query.count()
    
    # Pass percentage
    passed_results = Result.query.filter_by(pass_fail_status='pass').count()
    pass_percentage = round((passed_results / total_results) * 100, 1) if total_results > 0 else 0.0

    stats = {
        'total_students': total_students,
        'total_admins': total_admins,
        'total_exams': total_exams,
        'total_questions': total_questions,
        'active_exams': active_exams,
        'completed_exams': completed_exams,
        'total_results': total_results,
        'pass_rate': f"{pass_percentage}%"
    }

    # Widget widgets data
    recent_students = User.query.order_by(User.created_at.desc()).limit(5).all()
    upcoming_exams = Exam.query.filter(Exam.status == 'upcoming').order_by(Exam.exam_date).limit(5).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(5).all()
    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html', 
        stats=stats, 
        recent_students=recent_students,
        upcoming_exams=upcoming_exams,
        recent_activities=recent_activities,
        notifications=recent_notifications,
        system_status="Online"
    )


# --- Student Management ---
@admin_bp.route('/students')
@login_required
def students():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()
    year = request.args.get('year_of_study', '').strip()

    query = User.query
    if search:
        query = query.filter(User.full_name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    if dept:
        query = query.filter(User.department == dept)
    if year:
        query = query.filter(User.year_of_study == int(year))

    students_list = query.order_by(User.id).all()
    return render_template('admin/students.html', students=students_list)

@admin_bp.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    student = User.query.get_or_404(student_id)
    student_results = Result.query.filter_by(student_id=student_id).all()
    activities = ActivityLog.query.filter_by(user_id=student_id).order_by(ActivityLog.created_at.desc()).all()
    return render_template('admin/student_profile.html', student=student, results=student_results, activities=activities)

@admin_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = User.query.get_or_404(student_id)
    if request.method == 'POST':
        student.full_name = request.form.get('name', '').strip()
        student.phone_number = request.form.get('phone', '').strip() or None
        student.department = request.form.get('department', '').strip() or None
        
        year = request.form.get('year_of_study')
        student.year_of_study = int(year) if year else None
        
        db.session.commit()
        log_admin_activity(f"Edited student profile ID={student.id}")
        flash('Student profile updated successfully.', 'success')
        return redirect(url_for('admin.student_profile', student_id=student.id))
        
    return render_template('admin/edit_student.html', student=student) # Reuse edit form or handle inside student_profile

@admin_bp.route('/student/<int:student_id>/toggle-status', methods=['POST'])
@login_required
def toggle_student_status(student_id):
    student = User.query.get_or_404(student_id)
    student.status = not student.status
    db.session.commit()
    status_str = "activated" if student.status else "deactivated"
    log_admin_activity(f"Toggled student status to {status_str} for ID={student.id}")
    flash(f"Student account has been {status_str}.", 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    log_admin_activity(f"Deleted student account ID={student.id}")
    flash('Student account has been deleted.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/students/export')
@login_required
def export_students():
    students_list = User.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Department', 'Year of Study', 'Status', 'Verified'])
    for s in students_list:
        cw.writerow([s.id, s.full_name, s.email, s.phone_number, s.department, s.year_of_study, s.status, s.is_verified])
    
    output = BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='students_export.csv'
    )


# --- Exam Management ---
@admin_bp.route('/exams')
@login_required
def exams():
    exams_list = Exam.query.order_by(Exam.id.desc()).all()
    return render_template('admin/exams.html', exams=exams_list)

@admin_bp.route('/exam/add', methods=['GET', 'POST'])
@login_required
def add_exam():
    if request.method == 'POST':
        title = request.form.get('exam_title', '').strip()
        subject = request.form.get('subject_name', '').strip()
        desc_text = request.form.get('description', '').strip()
        duration = request.form.get('duration_minutes', '').strip()
        pass_mark = request.form.get('pass_mark', '').strip()
        exam_date_str = request.form.get('exam_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        # Simple conversions
        parsed_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None
        parsed_start = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
        parsed_end = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None

        new_exam = Exam(
            exam_title=title,
            subject_name=subject,
            description=desc_text,
            duration_minutes=int(duration),
            pass_mark=int(pass_mark),
            exam_date=parsed_date,
            start_time=parsed_start,
            end_time=parsed_end,
            created_by=current_user.id
        )
        db.session.add(new_exam)
        db.session.commit()
        log_admin_activity(f"Created Exam ID={new_exam.id} Title={title}")
        flash('Exam created successfully.', 'success')
        return redirect(url_for('admin.exams'))
        
    return render_template('admin/add_exam.html')

@admin_bp.route('/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if request.method == 'POST':
        exam.exam_title = request.form.get('exam_title', '').strip()
        exam.subject_name = request.form.get('subject_name', '').strip()
        exam.description = request.form.get('description', '').strip()
        exam.duration_minutes = int(request.form.get('duration_minutes'))
        exam.pass_mark = int(request.form.get('pass_mark'))
        
        exam_date_str = request.form.get('exam_date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        exam.exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None
        exam.start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
        exam.end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None
        exam.status = request.form.get('status', exam.status)

        db.session.commit()
        log_admin_activity(f"Edited Exam ID={exam.id}")
        flash('Exam configuration updated.', 'success')
        return redirect(url_for('admin.exams'))
        
    return render_template('admin/edit_exam.html', exam=exam)

@admin_bp.route('/exam/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    log_admin_activity(f"Deleted Exam ID={exam_id}")
    flash('Exam deleted successfully.', 'success')
    return redirect(url_for('admin.exams'))

@admin_bp.route('/exam/<int:exam_id>/toggle-status', methods=['POST'])
@login_required
def toggle_exam_status(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.status == 'upcoming':
        exam.status = 'ongoing'
    elif exam.status == 'ongoing':
        exam.status = 'completed'
    else:
        exam.status = 'upcoming'
    db.session.commit()
    log_admin_activity(f"Toggled status of Exam ID={exam_id} to {exam.status}")
    flash(f"Exam status updated to {exam.status}.", 'success')
    return redirect(url_for('admin.exams'))


# --- Question Bank ---
@admin_bp.route('/questions')
@login_required
def questions():
    exam_id = request.args.get('exam_id')
    if exam_id:
        questions_list = Question.query.filter_by(exam_id=int(exam_id)).all()
    else:
        questions_list = Question.query.all()
    exams_list = Exam.query.all()
    return render_template('admin/questions.html', questions=questions_list, exams=exams_list, selected_exam_id=exam_id)

@admin_bp.route('/question/add', methods=['GET', 'POST'])
@login_required
def add_question():
    if request.method == 'POST':
        exam_id = int(request.form.get('exam_id'))
        q_text = request.form.get('question_text', '').strip()
        q_type = request.form.get('question_type', 'mcq')
        diff = request.form.get('difficulty_level', 'medium')
        marks = int(request.form.get('marks', 1))
        correct = request.form.get('correct_answer', '').strip().upper()

        new_q = Question(
            exam_id=exam_id,
            question_text=q_text,
            question_type=q_type,
            difficulty_level=diff,
            marks=marks,
            correct_answer=correct
        )
        db.session.add(new_q)
        db.session.commit()

        # Add MCQ options if applicable
        if q_type == 'mcq':
            opt = Option(
                question_id=new_q.id,
                option_a=request.form.get('option_a', '').strip(),
                option_b=request.form.get('option_b', '').strip(),
                option_c=request.form.get('option_c', '').strip(),
                option_d=request.form.get('option_d', '').strip()
            )
            db.session.add(opt)
            db.session.commit()

        # Update exam question counts
        exam = Exam.query.get(exam_id)
        if exam:
            exam.total_questions = Question.query.filter_by(exam_id=exam_id).count()
            exam.total_marks = db.session.query(func.sum(Question.marks)).filter_by(exam_id=exam_id).scalar() or 0
            db.session.commit()

        log_admin_activity(f"Added Question ID={new_q.id} to Exam ID={exam_id}")
        flash('Question added to the exam bank.', 'success')
        return redirect(url_for('admin.questions', exam_id=exam_id))
        
    exams_list = Exam.query.all()
    return render_template('admin/add_question.html', exams=exams_list)

@admin_bp.route('/question/<int:q_id>/delete', methods=['POST'])
@login_required
def delete_question(q_id):
    q = Question.query.get_or_404(q_id)
    exam_id = q.exam_id
    db.session.delete(q)
    db.session.commit()
    
    # Recalculate exam metrics
    exam = Exam.query.get(exam_id)
    if exam:
        exam.total_questions = Question.query.filter_by(exam_id=exam_id).count()
        exam.total_marks = db.session.query(func.sum(Question.marks)).filter_by(exam_id=exam_id).scalar() or 0
        db.session.commit()

    log_admin_activity(f"Deleted Question ID={q_id}")
    flash('Question removed from database.', 'success')
    return redirect(url_for('admin.questions', exam_id=exam_id))


# --- Results & Reports ---
@admin_bp.route('/results')
@login_required
def results():
    search = request.args.get('search', '').strip()
    exam_id = request.args.get('exam_id')

    query = Result.query.join(User, Result.student_id == User.id).join(Exam, Result.exam_id == Exam.id)
    
    if search:
        query = query.filter(User.full_name.ilike(f"%{search}%") | Exam.exam_title.ilike(f"%{search}%"))
    if exam_id:
        query = query.filter(Result.exam_id == int(exam_id))

    results_list = query.order_by(Result.id.desc()).all()
    exams_list = Exam.query.all()
    return render_template('admin/results.html', results=results_list, exams=exams_list, selected_exam_id=exam_id)

@admin_bp.route('/results/export/excel')
@login_required
def export_results_excel():
    results_list = Result.query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Exam Results"
    
    # Excel Headers
    headers = ["Result ID", "Student Name", "Exam Title", "Total Marks", "Obtained Marks", "Percentage", "Grade", "Status", "Generated At"]
    ws.append(headers)
    
    for r in results_list:
        ws.append([
            r.id,
            r.student.full_name,
            r.exam.exam_title,
            r.total_marks,
            r.obtained_marks,
            float(r.percentage or 0.0),
            r.grade,
            r.pass_fail_status,
            r.generated_at.strftime('%Y-%m-%d %H:%M')
        ])
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='exam_results.xlsx'
    )

@admin_bp.route('/student/<int:student_id>/transcript')
@login_required
def download_transcript(student_id):
    student = User.query.get_or_404(student_id)
    results_list = Result.query.filter_by(student_id=student_id).all()
    
    serialized = []
    for r in results_list:
        serialized.append({
            'exam_title': r.exam.exam_title,
            'obtained_marks': r.obtained_marks,
            'total_marks': r.total_marks,
            'percentage': float(r.percentage or 0.0),
            'grade': r.grade or 'N/A',
            'status': r.pass_fail_status,
            'date': r.generated_at.strftime('%Y-%m-%d')
        })
        
    pdf_buffer = generate_results_pdf(student.full_name, serialized)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{student.full_name.replace(' ', '_')}_transcript.pdf"
    )


# --- Live Proctoring & Monitoring ---
@admin_bp.route('/monitoring')
@login_required
def monitoring():
    monitoring_list = ExamMonitoring.query.all()
    active_sessions = Attendance.query.filter(Attendance.logout_time.is_(None)).all()
    return render_template('admin/monitoring.html', monitoring=monitoring_list, active_sessions=active_sessions)

@admin_bp.route('/monitoring/force-submit/<int:student_id>/<int:exam_id>', methods=['POST'])
@login_required
def force_submit(student_id, exam_id):
    # Log force submission activity
    student = User.query.get(student_id)
    exam = Exam.query.get(exam_id)
    student_name = student.full_name if student else f"Student ID={student_id}"
    exam_title = exam.exam_title if exam else f"Exam ID={exam_id}"
    
    log_admin_activity(f"Force submitted exam '{exam_title}' for student '{student_name}'")
    
    # Mark logout time in attendance
    attendance_record = Attendance.query.filter_by(student_id=student_id, exam_id=exam_id, logout_time=None).first()
    if attendance_record:
        attendance_record.logout_time = datetime.utcnow()
        attendance_record.attendance_status = 'suspended'
        db.session.commit()
        
    flash('Exam has been force-submitted successfully.', 'success')
    return redirect(url_for('admin.monitoring'))


# --- Analytics Panel ---
@admin_bp.route('/analytics')
@login_required
def analytics():
    # Pass metrics directly from database functions
    perf_data = get_performance_data()
    subj_data = get_subject_analysis()
    pass_fail_data = get_pass_fail_statistics()
    part_data = get_exam_participation()
    activity_data = get_monthly_activity()
    lead_data = get_leaderboard_rankings()

    return render_template(
        'admin/analytics.html',
        perf_data=perf_data,
        subj_data=subj_data,
        pass_fail_data=pass_fail_data,
        part_data=part_data,
        activity_data=activity_data,
        lead_data=lead_data
    )


# --- Notifications ---
@admin_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        user_id_raw = request.form.get('user_id') # If None, then broadcast
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        notif_type = request.form.get('notification_type', 'system')

        if not (title and message):
            flash('Please enter a title and message.', 'danger')
            return redirect(url_for('admin.notifications'))

        try:
            if user_id_raw:
                # Direct Notification
                u_id = int(user_id_raw)
                notif = Notification(user_id=u_id, title=title, message=message, notification_type=notif_type)
                db.session.add(notif)
            else:
                # Broadcast Notification
                all_users = User.query.all()
                for u in all_users:
                    notif = Notification(user_id=u.id, title=title, message=message, notification_type=notif_type)
                    db.session.add(notif)
            
            db.session.commit()
            log_admin_activity(f"Created Notification: {title}")
            flash('Notification published successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"Error publishing notification: {e}", 'danger')

        return redirect(url_for('admin.notifications'))

    notifications_list = Notification.query.order_by(Notification.created_at.desc()).all()
    students_list = User.query.all()
    return render_template('admin/notifications.html', notifications=notifications_list, students=students_list)


# --- Certificates ---
@admin_bp.route('/certificates')
@login_required
def certificates():
    certs = Certificate.query.order_by(Certificate.generated_date.desc()).all()
    results_list = Result.query.filter_by(pass_fail_status='pass').all()
    return render_template('admin/certificates.html', certificates=certs, results=results_list)

@admin_bp.route('/certificate/generate', methods=['POST'])
@login_required
def generate_certificate():
    result_id = int(request.form.get('result_id'))
    result = Result.query.get_or_404(result_id)
    
    # Check if certificate already exists
    existing = Certificate.query.filter_by(student_id=result.student_id, exam_id=result.exam_id).first()
    if existing:
        flash('Certificate already exists for this student and exam.', 'info')
        return redirect(url_for('admin.certificates'))

    try:
        cert_num = f"CERT-{result.exam_id:03d}-{result.student_id:04d}-{datetime.utcnow().strftime('%y%m%d')}"
        
        # Create validation link for QR Code
        val_link = f"http://127.0.0.1:5000/verify/certificate/{cert_num}"
        qr_b64 = generate_qr_code_base64(val_link)

        new_cert = Certificate(
            student_id=result.student_id,
            exam_id=result.exam_id,
            certificate_number=cert_num,
            qr_code=qr_b64
        )
        db.session.add(new_cert)
        db.session.commit()

        log_admin_activity(f"Generated Certificate: {cert_num}")
        flash('Certificate generated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to generate certificate: {e}", 'danger')
        
    return redirect(url_for('admin.certificates'))

@admin_bp.route('/certificate/<int:cert_id>/download')
@login_required
def download_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    issue_date_str = cert.generated_date.strftime('%Y-%m-%d')
    
    # Verify score
    result = Result.query.filter_by(student_id=cert.student_id, exam_id=cert.exam_id).first()
    score = float(result.percentage) if result else 0.0
    
    pdf_buffer = generate_certificate_pdf(
        student_name=cert.student.full_name,
        exam_title=cert.exam.exam_title,
        score=score,
        certificate_number=cert.certificate_number,
        issue_date=issue_date_str,
        qr_base64=cert.qr_code
    )
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Certificate_{cert.certificate_number}.pdf"
    )


# --- Attendance ---
@admin_bp.route('/attendance')
@login_required
def attendance():
    attendance_list = Attendance.query.order_by(Attendance.login_time.desc()).all()
    return render_template('admin/attendance.html', attendance=attendance_list)


# --- Activity Logs ---
@admin_bp.route('/activity-logs')
@login_required
def activity_logs():
    role = request.args.get('role', '').strip()
    query = ActivityLog.query
    if role:
        query = query.filter(ActivityLog.user_role == role)
    logs = query.order_by(ActivityLog.created_at.desc()).all()
    return render_template('admin/activity_logs.html', logs=logs, selected_role=role)


# --- Settings ---
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Admin password updates
        cur_pwd = request.form.get('current_password')
        new_pwd = request.form.get('new_password')
        conf_pwd = request.form.get('confirm_password')

        admin = Admin.query.get(current_user.id)
        if not admin:
            flash('Admin account invalid.', 'danger')
            return redirect(url_for('admin.settings'))

        if bcrypt.check_password_hash(admin.password, cur_pwd):
            if new_pwd == conf_pwd:
                hashed = bcrypt.generate_password_hash(new_pwd).decode('utf-8')
                admin.password = hashed
                db.session.commit()
                log_admin_activity('Admin changed password')
                flash('Administrator password updated successfully.', 'success')
            else:
                flash('New passwords do not match.', 'danger')
        else:
            flash('Incorrect current administrator password.', 'danger')
            
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html')
