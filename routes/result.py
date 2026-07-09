import io
import csv
import openpyxl
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import login_required, current_user
from database import db
from models import (User, Admin, Exam, Question, Option, StudentAnswer, Result, 
                    Attendance, ExamMonitoring, Certificate, Notification, ActivityLog, Leaderboard, Analytics)
from utils.result_calculator import calculate_attempt_details
from utils.chart_generator import get_student_chart_data, get_admin_chart_data
from utils.pdf_generator import generate_individual_result_pdf
from utils.qr_generator import generate_qr_code_base64
from utils.charts import predict_next_score_ai, analyze_weak_strong_subjects

result_bp = Blueprint('result', __name__, url_prefix='/result')

@result_bp.before_request
@login_required
def check_role_auth():
    """
    Enforces student authentication for student result routes.
    """
    if not isinstance(current_user, User):
        flash('Access denied. Student authorization required.', 'danger')
        return redirect(url_for('auth.login'))

@result_bp.route('/results')
def results_list():
    """
    Displays list of all exams taken by the student.
    """
    results = Result.query.filter_by(student_id=current_user.id).order_by(Result.generated_at.desc()).all()
    return render_template('student/results.html', results=results)

@result_bp.route('/result-details/<int:result_id>')
def result_details(result_id):
    """
    Displays a comprehensive attempt review, including question key breakdowns
    and explanations.
    """
    res = Result.query.get_or_404(result_id)
    if res.student_id != current_user.id:
        flash('Access denied. Unauthorized to view this report.', 'danger')
        return redirect(url_for('result.results_list'))
        
    calc = calculate_attempt_details(current_user.id, res.exam_id)
    
    # Load all questions & student answers
    questions = Question.query.filter_by(exam_id=res.exam_id).all()
    answers = StudentAnswer.query.filter_by(student_id=current_user.id, exam_id=res.exam_id).all()
    answers_map = {ans.question_id: ans for ans in answers}
    
    return render_template(
        'student/result_details.html',
        result=res,
        calc=calc,
        questions=questions,
        answers_map=answers_map
    )

@result_bp.route('/analytics')
def analytics_view():
    return redirect(url_for('analytics_bp.index'))

@result_bp.route('/leaderboard')
def leaderboard_view():
    """
    Displays overall ranks.
    """
    # Dynamic leaderboard rankings: Group total marks from past attempts
    # We select all students, compute their sum of obtained marks, and rank them.
    subquery = db.session.query(
        Result.student_id,
        db.func.sum(Result.obtained_marks).label('total_points')
    ).group_by(Result.student_id).subquery()
    
    rankings = db.session.query(
        User,
        subquery.c.total_points
    ).join(User, User.id == subquery.c.student_id)\
     .order_by(subquery.c.total_points.desc()).all()
     
    # Convert list of tuples to formatted list of rank cards
    leaderboard_list = []
    student_rank = "N/A"
    
    for idx, (usr, total_pts) in enumerate(rankings):
        rank = idx + 1
        if usr.id == current_user.id:
            student_rank = rank
            
        leaderboard_list.append({
            "rank": rank,
            "name": usr.full_name,
            "department": usr.department or "Computer Science",
            "score": total_pts
        })
        
    return render_template(
        'student/leaderboard.html',
        leaderboard=leaderboard_list,
        student_rank=student_rank
    )

@result_bp.route('/certificates')
def certificates_view():
    """
    List certificates earned by student.
    """
    certs = Certificate.query.filter_by(student_id=current_user.id).order_by(Certificate.generated_date.desc()).all()
    return render_template('student/certificates.html', certificates=certs)

@result_bp.route('/download-report')
def download_report_landing():
    """
    Landing options page for exports.
    """
    results = Result.query.filter_by(student_id=current_user.id).all()
    return render_template('student/download_report.html', results_count=len(results))

@result_bp.route('/export/excel')
def export_excel():
    """
    Generates and downloads an Excel workbook containing academic transcripts.
    """
    results = Result.query.filter_by(student_id=current_user.id).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Academic Transcripts"
    
    # Write metadata headers
    ws.append(["EduExam Academic Transcript", ""])
    ws.append(["Student Name:", current_user.full_name])
    ws.append(["Email:", current_user.email])
    ws.append(["Date Generated:", datetime.now().strftime('%Y-%m-%d')])
    ws.append([]) # spacer
    
    # Table headers
    ws.append(["Exam Title", "Subject", "Total Marks", "Obtained Marks", "Percentage", "Grade", "Status", "Exam Date"])
    
    for r in results:
        ws.append([
            r.exam.exam_title,
            r.exam.subject_name,
            r.total_marks,
            r.obtained_marks,
            f"{r.percentage}%",
            r.grade,
            r.pass_fail_status.upper(),
            r.generated_at.strftime('%Y-%m-%d')
        ])
        
    # Autofil width
    for col in ws.columns:
        max_len = max(len(str(val.value or '')) for val in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 10)
        
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    
    return send_file(
        out,
        as_attachment=True,
        download_name="academic_transcript.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@result_bp.route('/export/csv')
def export_csv():
    """
    Generates and downloads a CSV report containing student results.
    """
    results = Result.query.filter_by(student_id=current_user.id).all()
    
    out = io.StringIO()
    writer = csv.writer(out)
    
    writer.writerow(["Exam Title", "Subject", "Total Marks", "Obtained Marks", "Percentage", "Grade", "Status", "Date Taken"])
    for r in results:
        writer.writerow([
            r.exam.exam_title,
            r.exam.subject_name,
            r.total_marks,
            r.obtained_marks,
            f"{r.percentage}%",
            r.grade,
            r.pass_fail_status.upper(),
            r.generated_at.strftime('%Y-%m-%d')
        ])
        
    mem = io.BytesIO(out.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name="academic_transcript.csv",
        mimetype="text/csv"
    )

@result_bp.route('/pdf/<int:result_id>')
def download_pdf_report(result_id):
    """
    Generates and streams a ReportLab PDF document for a single result.
    """
    res = Result.query.get_or_404(result_id)
    if res.student_id != current_user.id:
        flash('Unauthorized PDF request.', 'danger')
        return redirect(url_for('result.results_list'))
        
    calc = calculate_attempt_details(current_user.id, res.exam_id)
    scorecard = {
        "obtained_marks": res.obtained_marks,
        "total_marks": res.total_marks,
        "percentage": res.percentage,
        "grade": res.grade,
        "rank": calc.get("rank", 1),
        "pass_fail_status": res.pass_fail_status,
        "total_questions": calc.get("total_questions", 0),
        "correct_answers": calc.get("correct_answers", 0),
        "wrong_answers": calc.get("wrong_answers", 0),
        "skipped_questions": calc.get("skipped_questions", 0),
        "duration_minutes": res.exam.duration_minutes,
        "date_taken": res.created_at.strftime('%Y-%m-%d %H:%M')
    }
    
    # Generate QR verification link base64
    # Create verification landing endpoint string or certificate number
    cert = Certificate.query.filter_by(student_id=current_user.id, exam_id=res.exam_id).first()
    qr_data = cert.qr_code if cert else f"Verification ID: OES-{res.id}"
    qr_base64 = generate_qr_code_base64(qr_data)
    
    buffer = generate_individual_result_pdf(
        student_name=current_user.full_name,
        student_email=current_user.email,
        department=current_user.department,
        year=current_user.year_of_study,
        exam_title=res.exam.exam_title,
        subject_name=res.exam.subject_name,
        scorecard=scorecard,
        qr_base64=qr_base64
    )
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"result_{res.exam.exam_title.replace(' ', '_')}.pdf",
        mimetype="application/pdf"
    )
