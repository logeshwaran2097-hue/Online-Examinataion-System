from flask import Blueprint, redirect, url_for
from models import Result

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def student_dashboard():
    return redirect(url_for('student.dashboard'))

@dashboard_bp.route('/exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    return redirect(url_for('student.take_exam', exam_id=exam_id))

@dashboard_bp.route('/result/<int:result_id>')
def exam_result(result_id):
    res = Result.query.get(result_id)
    if res:
        return redirect(url_for('student.review_exam', exam_id=res.exam_id, result_id=result_id))
    return redirect(url_for('student.results'))

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    return redirect(url_for('student.profile'))
