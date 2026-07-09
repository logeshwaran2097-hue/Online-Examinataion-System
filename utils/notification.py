from database import db
from models import Notification

def dispatch_notification(user_id, title, message, notification_type='system'):
    """
    Creates and saves a database notification record for a specific user.
    """
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"Error dispatching notification: {e}")
        return None

def notify_exam_reminder(user_id, exam_title, start_time_str):
    """
    Dispatches a scheduled exam reminder alert.
    """
    title = "Upcoming Exam Reminder"
    message = f"Reminder: Your scheduled exam '{exam_title}' is set to start at {start_time_str}. Please prepare your webcam proctoring settings."
    return dispatch_notification(user_id, title, message, notification_type='exam')

def notify_result_release(user_id, exam_title, score_pct, grade):
    """
    Dispatches exam results grading notification notes.
    """
    title = "Exam Result Released"
    message = f"Your attempt scorecard for '{exam_title}' is ready. Obtained: {score_pct}%. Grade: {grade}."
    return dispatch_notification(user_id, title, message, notification_type='result')
