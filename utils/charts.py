from sqlalchemy import func, desc
from database import db
from models import Result, Exam, User, Analytics, Leaderboard
from datetime import datetime, timedelta

def get_student_academic_summary(student_id):
    """
    Computes key metrics for the student's statistics cards.
    """
    # 1. Total Exams Available
    # An exam is available if its status is 'upcoming' or 'ongoing'
    total_available = Exam.query.filter(Exam.status.in_(['upcoming', 'ongoing'])).count()
    
    # 2. Exams Completed by the student
    total_completed = Result.query.filter_by(student_id=student_id).count()
    
    # 3. Upcoming Exams
    upcoming_exams = Exam.query.filter(Exam.status == 'upcoming').count()
    
    # 4. Average Score
    avg_score_res = db.session.query(func.avg(Result.percentage)).filter_by(student_id=student_id).scalar()
    avg_score = round(float(avg_score_res), 2) if avg_score_res else 0.0
    
    # 5. Leaderboard Rank
    rank_res = Leaderboard.query.filter_by(student_id=student_id).first()
    current_rank = rank_res.rank_position if rank_res else None
    
    # 6. Certificates Earned
    from models.certificate import Certificate
    certs_earned = Certificate.query.filter_by(student_id=student_id).count()
    
    return {
        "total_available": total_available,
        "exams_completed": total_completed,
        "upcoming_exams": upcoming_exams,
        "average_score": avg_score,
        "current_rank": current_rank or "N/A",
        "certificates_earned": certs_earned
    }

def get_student_progress_chart(student_id):
    """
    Retrieves student attempts chronologically.
    Returns labels (exam names/dates) and values (scores) for a line chart.
    """
    attempts = db.session.query(
        Exam.exam_title,
        Result.percentage,
        Result.generated_at
    ).join(Result, Exam.id == Result.exam_id)\
     .filter(Result.student_id == student_id)\
     .order_by(Result.generated_at.asc()).all()
     
    labels = []
    scores = []
    
    for i, att in enumerate(attempts):
        # Format label like "Quiz 1 (06-25)" or similar
        date_str = att.generated_at.strftime('%m-%d')
        labels.append(f"{att.exam_title[:15]} ({date_str})")
        scores.append(float(att.percentage))
        
    # If no attempts, provide default mock guide
    if not labels:
        labels = ["Start"]
        scores = [0.0]
        
    return {
        "labels": labels,
        "values": scores
    }

def get_subject_performance(student_id):
    """
    Subject-wise average score analytics.
    Suitable for Radar / Bar Chart.
    """
    subjects = db.session.query(
        Exam.subject_name,
        func.avg(Result.percentage).label('avg_score'),
        func.count(Result.id).label('exams_taken')
    ).join(Result, Exam.id == Result.exam_id)\
     .filter(Result.student_id == student_id)\
     .group_by(Exam.subject_name)\
     .order_by(desc('avg_score')).all()
     
    labels = [s.subject_name for s in subjects]
    values = [round(float(s.avg_score), 2) for s in subjects]
    
    return {
        "labels": labels,
        "values": values,
        "records": [{
            "subject": s.subject_name,
            "avg_score": round(float(s.avg_score), 2),
            "count": s.exams_taken
        } for s in subjects]
    }

def analyze_weak_strong_subjects(student_id):
    """
    Determines strongest and weakest subjects for the student.
    """
    subject_data = get_subject_performance(student_id)["records"]
    if not subject_data:
        return {"strongest": "N/A", "weakest": "N/A"}
        
    # Sorted by average score desc
    strongest = subject_data[0]["subject"]
    weakest = subject_data[-1]["subject"]
    
    return {
        "strongest": strongest,
        "weakest": weakest
    }

def predict_next_score_ai(student_id):
    """
    AI Performance Prediction:
    Computes a linear regression trend line over chronological scores to predict the next score.
    Returns: (predicted_score, trend_direction)
    """
    attempts = db.session.query(Result.percentage)\
     .filter(Result.student_id == student_id)\
     .order_by(Result.generated_at.asc()).all()
     
    scores = [float(att.percentage) for att in attempts]
    n = len(scores)
    
    if n == 0:
        return 75.0, "stable"  # Default fallback for new students
    elif n == 1:
        return scores[0], "stable"
        
    # Simple linear regression
    # x = [1, 2, ..., n]
    x = list(range(1, n + 1))
    y = scores
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(px * py for px, py in zip(x, y))
    sum_x_squared = sum(px**2 for px in x)
    
    numerator = (n * sum_xy) - (sum_x * sum_y)
    denominator = (n * sum_x_squared) - (sum_x**2)
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
        
    intercept = (sum_y - slope * sum_x) / n
    
    # Predict next step (n + 1)
    predicted = slope * (n + 1) + intercept
    
    # Bound the score
    predicted = max(0.0, min(100.0, predicted))
    
    trend = "improving" if slope > 0.5 else "declining" if slope < -0.5 else "stable"
    return round(predicted, 2), trend
