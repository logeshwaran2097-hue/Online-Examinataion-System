from sqlalchemy.sql import func
from database import db
from models import Result, Exam, StudentAnswer, Question, Leaderboard, User

def get_student_chart_data(student_id):
    """
    Aggregates analytical metrics and history progress charts for a student.
    """
    # 1. Monthly Score Trend
    results = Result.query.filter_by(student_id=student_id).order_by(Result.generated_at.asc()).all()
    trend_labels = []
    trend_scores = []
    
    for r in results:
        trend_labels.append(r.exam.exam_title[:15] + '...')
        trend_scores.append(round(r.percentage, 1))
        
    # 2. Subject-wise Averages
    subject_stats = db.session.query(
        Exam.subject_name,
        func.avg(Result.percentage).label('avg_score')
    ).join(Result, Result.exam_id == Exam.id)\
     .filter(Result.student_id == student_id)\
     .group_by(Exam.subject_name).all()
     
    subject_labels = [stat.subject_name for stat in subject_stats]
    subject_scores = [round(stat.avg_score, 1) for stat in subject_stats]
    
    # 3. Accuracy calculations (Correct answers / Total questions attempted)
    total_answers = StudentAnswer.query.filter_by(student_id=student_id).count()
    correct_answers = StudentAnswer.query.filter_by(student_id=student_id, answer_status=True).count()
    accuracy_pct = round((correct_answers / total_answers * 100.0), 1) if total_answers > 0 else 0.0
    
    # 4. Pass vs Fail distribution
    passes = Result.query.filter_by(student_id=student_id, pass_fail_status='pass').count()
    fails = Result.query.filter_by(student_id=student_id, pass_fail_status='fail').count()
    
    return {
        "trend_labels": trend_labels,
        "trend_scores": trend_scores,
        "subject_labels": subject_labels,
        "subject_scores": subject_scores,
        "accuracy_pct": accuracy_pct,
        "pass_count": passes,
        "fail_count": fails
    }

def get_admin_chart_data():
    """
    Aggregates analytical metrics for administrators.
    """
    # Pass Percentage globally
    total_results = Result.query.count()
    pass_count = Result.query.filter_by(pass_fail_status='pass').count()
    global_pass_pct = round((pass_count / total_results * 100.0), 1) if total_results > 0 else 0.0
    
    # Department standings
    dept_stats = db.session.query(
        User.department,
        func.avg(Result.percentage).label('avg_score'),
        func.count(Result.id).label('exams_count')
    ).join(Result, Result.student_id == User.id)\
     .group_by(User.department).all()
     
    dept_labels = [stat.department for stat in dept_stats if stat.department]
    dept_scores = [round(stat.avg_score, 1) for stat in dept_stats if stat.department]
    
    return {
        "global_pass_pct": global_pass_pct,
        "dept_labels": dept_labels,
        "dept_scores": dept_scores,
        "total_attempts": total_results
    }
