from models import StudentAnswer

def get_student_saved_answers_map(student_id, exam_id):
    """
    Retrieves all previously auto-saved answers for the student's active exam session.
    Returns: A dictionary mapping question_id (int) to the selected option string.
    """
    answers = StudentAnswer.query.filter_by(student_id=student_id, exam_id=exam_id).all()
    # Map question_id to the selected answer option
    return {ans.question_id: ans.selected_answer for ans in answers if ans.selected_answer}

def get_completed_questions_count(student_id, exam_id):
    """
    Returns the count of questions the student has already answered.
    """
    answers = get_student_saved_answers_map(student_id, exam_id)
    return len(answers)
