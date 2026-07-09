"""
utils/exam_submission.py
========================
Shared exam submission engine — centralizes all result calculation,
certificate generation, and notification logic.

Both student.py and exam.py should delegate to this module so the
logic lives in exactly ONE place and is easier to maintain/fix.
"""
from datetime import datetime
from flask import request
from database import db
from models import (
    Question, StudentAnswer, Attendance, Result,
    Certificate, Notification, ActivityLog
)
from utils.certificate_generator import generate_unique_certificate_number


def _compute_grade(percentage: float) -> str:
    if percentage >= 90: return 'A+'
    if percentage >= 80: return 'A'
    if percentage >= 70: return 'B'
    if percentage >= 60: return 'C'
    if percentage >= 50: return 'D'
    return 'F'


def _log_audit(student_id: int, activity: str):
    try:
        log = ActivityLog(
            user_id=student_id,
            user_role='student',
            activity=activity,
            ip_address=request.remote_addr or 'unknown',
            browser=request.user_agent.string[:255] or 'unknown'
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def process_exam_submission(student_id: int, exam_id, exam, is_auto: bool = False) -> Result:
    """
    Core submission engine called by BOTH student blueprint and exam blueprint.

    1. Marks attendance logout time
    2. Calculates score
    3. Creates the Result row
    4. Generates certificate if student passed
    5. Sends notifications
    6. Logs audit trail

    Returns the saved Result object.
    """
    # ── 1. Close attendance record ────────────────────────────
    attendance = Attendance.query.filter_by(
        student_id=student_id, exam_id=exam_id
    ).first()
    if attendance and attendance.logout_time is None:
        attendance.logout_time = datetime.utcnow()

    # ── 2. Score calculation ──────────────────────────────────
    questions = Question.query.filter_by(exam_id=exam_id).all()
    total_marks = sum(q.marks for q in questions)
    obtained_marks = 0

    user_answers = StudentAnswer.query.filter_by(
        student_id=student_id, exam_id=exam_id
    ).all()
    answers_map = {ans.question_id: ans.selected_answer for ans in user_answers}

    for q in questions:
        if answers_map.get(q.id) == q.correct_answer:
            obtained_marks += q.marks

    percentage = round((obtained_marks / total_marks * 100.0), 2) if total_marks > 0 else 0.0
    grade = _compute_grade(percentage)
    pass_fail = 'pass' if obtained_marks >= exam.pass_mark else 'fail'

    # ── 3. Create Result record ───────────────────────────────
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

    # ── 4. Auto-generate certificate if passed ────────────────
    if pass_fail == 'pass':
        existing_cert = Certificate.query.filter_by(
            student_id=student_id, exam_id=exam_id
        ).first()
        if not existing_cert:
            cert_num = generate_unique_certificate_number()
            host_url = request.host_url.rstrip('/')
            verif_url = f"{host_url}/student/verify-certificate/{cert_num}"

            cert = Certificate(
                student_id=student_id,
                exam_id=exam_id,
                certificate_number=cert_num,
                qr_code=verif_url
            )
            db.session.add(cert)

            cert_notif = Notification(
                user_id=student_id,
                title="Certificate Awarded!",
                message=(
                    f"Congratulations! You passed '{exam.exam_title}' "
                    f"and earned Certificate: {cert_num}."
                ),
                notification_type="result"
            )
            db.session.add(cert_notif)

    # ── 5. Result notification ────────────────────────────────
    mode = " (auto-submitted)" if is_auto else ""
    res_notif = Notification(
        user_id=student_id,
        title="Exam Result Ready",
        message=(
            f"Your score for '{exam.exam_title}' is "
            f"{percentage}% — {pass_fail.upper()}{mode}."
        ),
        notification_type="result"
    )
    db.session.add(res_notif)
    db.session.commit()

    # ── 6. Audit log ──────────────────────────────────────────
    _log_audit(
        student_id,
        f"Submitted exam '{exam.exam_title}' "
        f"(Score: {obtained_marks}/{total_marks}, Auto: {is_auto})"
    )

    return res
