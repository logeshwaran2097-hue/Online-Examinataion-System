from sqlalchemy import func, desc
from database import db
from models import User, Exam, Result, Leaderboard, Attendance, ActivityLog
from datetime import datetime, timedelta

def get_performance_data():
    """
    Get average percentage score across all exams.
    Returns: list of dicts with exam title and average score.
    """
    results = db.session.query(
        Exam.exam_title,
        func.avg(Result.percentage).label('avg_score')
    ).join(Result, Exam.id == Result.exam_id)\
     .group_by(Exam.exam_title)\
     .order_by(Exam.exam_title).all()
     
    return [{'label': r.exam_title, 'value': float(r.avg_score or 0.0)} for r in results]

def get_subject_analysis():
    """
    Get subject-wise performance analytics.
    Returns: list of dicts with subject name, total exams, average score.
    """
    results = db.session.query(
        Exam.subject_name,
        func.count(Result.id).label('total_attempts'),
        func.avg(Result.percentage).label('avg_score')
    ).join(Result, Exam.id == Result.exam_id)\
     .group_by(Exam.subject_name)\
     .order_by(desc('total_attempts')).all()
     
    return [{
        'subject': r.subject_name,
        'attempts': r.total_attempts,
        'avg_score': float(r.avg_score or 0.0)
    } for r in results]

def get_pass_fail_statistics():
    """
    Get global counts of pass vs fail results.
    """
    results = db.session.query(
        Result.pass_fail_status,
        func.count(Result.id).label('count')
    ).group_by(Result.pass_fail_status).all()
    
    data = {'pass': 0, 'fail': 0}
    for r in results:
        status = (r.pass_fail_status or '').lower()
        if status in ['pass', 'fail']:
            data[status] = r.count
    return data

def get_exam_participation():
    """
    Get daily/monthly exam participation counts (attendance check-ins).
    For the past 30 days.
    """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Cast timestamp to date for grouping
    participation = db.session.query(
        func.date(Attendance.login_time).label('date'),
        func.count(Attendance.id).label('count')
    ).filter(Attendance.login_time >= thirty_days_ago)\
     .group_by(func.date(Attendance.login_time))\
     .order_by(func.date(Attendance.login_time)).all()
     
    return [{'date': str(p.date), 'count': p.count} for p in participation]

def get_monthly_activity():
    """
    Get action volume from activity_logs grouped by activity count.
    For the past 7 days to keep it compact and highly responsive.
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs = db.session.query(
        func.date(ActivityLog.created_at).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(ActivityLog.created_at >= seven_days_ago)\
     .group_by(func.date(ActivityLog.created_at))\
     .order_by(func.date(ActivityLog.created_at)).all()
     
    return [{'date': str(l.date), 'count': l.count} for l in logs]

def get_leaderboard_rankings(limit=10):
    """
    Get student leaderboard rankings.
    """
    rankings = db.session.query(
        User.full_name,
        User.department,
        Leaderboard.total_score,
        Leaderboard.rank_position
    ).join(Leaderboard, User.id == Leaderboard.student_id)\
     .order_by(Leaderboard.rank_position).limit(limit).all()
     
    return [{
        'name': r.full_name,
        'department': r.department or 'General',
        'score': r.total_score,
        'rank': r.rank_position
    } for r in rankings]
