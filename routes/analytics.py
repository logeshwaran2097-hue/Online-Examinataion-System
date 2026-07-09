from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User
from utils.prediction import predict_future_performance
from utils.charts import analyze_weak_strong_subjects
from utils.chart_generator import get_student_chart_data
from utils.ai_engine import get_personalized_question_recommendations

analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/analytics')

@analytics_bp.before_request
@login_required
def check_role_auth():
    if not isinstance(current_user, User):
        flash('Access denied. Student authorization required.', 'danger')
        return redirect(url_for('auth.login'))

@analytics_bp.route('/')
def index():
    """
    Renders dynamic performance analysis, ML predictions, and AI recommendations.
    """
    predicted_stats = predict_future_performance(current_user.id)
    subjects_info = analyze_weak_strong_subjects(current_user.id)
    chart_data = get_student_chart_data(current_user.id)
    
    # AI recommendations
    recs = get_personalized_question_recommendations(current_user.id)
    
    return render_template(
        'student/analytics.html',
        predicted_score=predicted_stats.get("predicted_score"),
        trend=predicted_stats.get("improvement_rate"),
        strongest=subjects_info.get("strongest", "N/A"),
        weakest=subjects_info.get("weakest", "N/A"),
        chart_data=chart_data,
        recommendations=recs
    )

@analytics_bp.route('/recommendations')
def recommendations_view():
    """
    Personalized practice question bank.
    """
    recs = get_personalized_question_recommendations(current_user.id)
    return render_template('student/practice_recommendation.html', recommendations=recs)
