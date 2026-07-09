from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models import User, Result

leaderboard_bp = Blueprint('leaderboard_bp', __name__, url_prefix='/leaderboard')

@leaderboard_bp.before_request
@login_required
def check_role_auth():
    if not isinstance(current_user, User):
        flash('Access denied. Student authorization required.', 'danger')
        return redirect(url_for('auth.login'))

@leaderboard_bp.route('/')
def index():
    """
    Renders rankings board.
    """
    subquery = db.session.query(
        Result.student_id,
        db.func.sum(Result.obtained_marks).label('total_points')
    ).group_by(Result.student_id).subquery()
    
    rankings = db.session.query(
        User,
        subquery.c.total_points
    ).join(User, User.id == subquery.c.student_id)\
     .order_by(subquery.c.total_points.desc()).all()
     
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
