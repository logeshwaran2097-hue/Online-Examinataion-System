from database import db
from models import Question, Exam, Result
from utils.charts import analyze_weak_strong_subjects, get_subject_performance

def get_personalized_question_recommendations(student_id):
    """
    Analyzes historical scores to recommend tailored practice questions
    based on subject-wise mastery level and difficulty thresholds.
    """
    subject_diagnostics = analyze_weak_strong_subjects(student_id)
    weak_subject = subject_diagnostics.get("weakest")
    
    if not weak_subject or weak_subject == "N/A":
        # Default fallback recommendations if no exams have been taken
        default_questions = Question.query.filter_by(difficulty_level='easy').limit(5).all()
        return {
            "weak_subject": "General Computer Science",
            "recommended_difficulty": "easy",
            "recommended_questions": default_questions,
            "recommended_topics": ["Data Structures Introduction", "Variables & Types", "Control Flows"]
        }
        
    # Determine proficiency percentage
    subject_details = get_subject_performance(student_id)["records"]
    avg_score = 0.0
    for row in subject_details:
        if row["subject"] == weak_subject:
            avg_score = row["avg_score"]
            break
            
    # Map average score to recommended difficulty level
    if avg_score < 50.0:
        target_diff = 'easy'
    elif avg_score < 75.0:
        target_diff = 'medium'
    else:
        target_diff = 'hard'
        
    # Query database questions in weak subject matching the recommended difficulty level
    recommended_questions = Question.query.join(Exam, Exam.id == Question.exam_id)\
     .filter(Exam.subject_name == weak_subject, Question.difficulty_level == target_diff)\
     .limit(5).all()
     
    # If no questions match the target difficulty, fall back to any questions in that subject
    if not recommended_questions:
        recommended_questions = Question.query.join(Exam, Exam.id == Question.exam_id)\
         .filter(Exam.subject_name == weak_subject)\
         .limit(5).all()
         
    # Compile topic ideas list based on subject
    topics = []
    if "Computer" in weak_subject or "CS" in weak_subject or "Structures" in weak_subject:
        topics = ["Binary Search Trees", "Sorting Algorithms Complexity", "Recursive Calls & Stacks"]
    elif "Database" in weak_subject or "SQL" in weak_subject or "DBMS" in weak_subject:
        topics = ["Database Normalization (3NF)", "Outer Joins & Group By Queries", "Transaction Isolation Levels"]
    else:
        topics = ["Foundational Concepts Review", "Subject Terminology Keys", "Logical Assessments Practice"]
        
    return {
        "weak_subject": weak_subject,
        "recommended_difficulty": target_diff,
        "recommended_questions": recommended_questions,
        "recommended_topics": topics
    }
