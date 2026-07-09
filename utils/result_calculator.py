from models import Exam, Question, StudentAnswer, Result, Leaderboard

def calculate_attempt_details(student_id, exam_id):
    """
    Computes attempt analytics for a student on a specific exam.
    Returns a dictionary of metrics.
    """
    exam = Exam.query.get(exam_id)
    if not exam:
        return {}
        
    questions = Question.query.filter_by(exam_id=exam_id).all()
    student_answers = StudentAnswer.query.filter_by(student_id=student_id, exam_id=exam_id).all()
    
    answers_map = {ans.question_id: ans.selected_answer for ans in student_answers}
    
    total_questions = len(questions)
    correct_answers = 0
    wrong_answers = 0
    skipped_questions = 0
    obtained_marks = 0
    total_marks = 0
    
    for q in questions:
        total_marks += q.marks
        sel = answers_map.get(q.id)
        
        if not sel:
            skipped_questions += 1
        elif sel == q.correct_answer:
            correct_answers += 1
            obtained_marks += q.marks
        else:
            wrong_answers += 1
            
    percentage = (obtained_marks / total_marks * 100.0) if total_marks > 0 else 0.0
    percentage = round(percentage, 2)
    
    # Grade Criteria
    if percentage >= 90: grade = 'A+'
    elif percentage >= 80: grade = 'A'
    elif percentage >= 70: grade = 'B'
    elif percentage >= 60: grade = 'C'
    elif percentage >= 50: grade = 'D'
    else: grade = 'F'
    
    pass_fail_status = 'pass' if obtained_marks >= exam.pass_mark else 'fail'
    
    # Calculate Rank dynamically based on results score descending
    dynamic_rank = 1
    # Count how many students scored higher than this student on this exam
    higher_results_count = Result.query.filter(
        Result.exam_id == exam_id,
        Result.obtained_marks > obtained_marks
    ).count()
    dynamic_rank += higher_results_count
    
    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "skipped_questions": skipped_questions,
        "obtained_marks": obtained_marks,
        "total_marks": total_marks,
        "percentage": percentage,
        "grade": grade,
        "pass_fail_status": pass_fail_status,
        "rank": dynamic_rank
    }
