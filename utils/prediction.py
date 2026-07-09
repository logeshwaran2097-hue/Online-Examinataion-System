import math
from models import Result

def predict_future_performance(student_id, pass_mark=50):
    """
    Predicts the student's next score and their pass probability
    using a mathematical regression slope model.
    """
    attempts = Result.query.filter_by(student_id=student_id).order_by(Result.generated_at.asc()).all()
    scores = [float(r.percentage) for r in attempts]
    n = len(scores)
    
    # Defaults for new students
    if n == 0:
        return {
            "predicted_score": 75.0,
            "pass_probability": 90.0,
            "improvement_rate": 0.0,
            "suggestions": [
                "Take your first examination to initialize performance prediction models.",
                "Review subject-wise question bank topics for active preparation."
            ]
        }
    elif n == 1:
        single_score = scores[0]
        # Sigmoid probability
        prob = 1.0 / (1.0 + math.exp(-0.15 * (single_score - pass_mark)))
        return {
            "predicted_score": single_score,
            "pass_probability": round(prob * 100.0, 1),
            "improvement_rate": 0.0,
            "suggestions": [
                "Attempt more exams to establish a progress history timeline.",
                "Practice weak subjects to steady your average scores."
            ]
        }
        
    # Standard regression fit
    x = list(range(1, n + 1))
    y = scores
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(px * py for px, py in zip(x, y))
    sum_x_squared = sum(px**2 for px in x)
    
    numerator = (n * sum_xy) - (sum_x * sum_y)
    denominator = (n * sum_x_squared) - (sum_x**2)
    
    slope = (numerator / denominator) if denominator != 0 else 0.0
    intercept = (sum_y - slope * sum_x) / n
    
    # Predict next step (n + 1)
    predicted_score = slope * (n + 1) + intercept
    predicted_score = max(0.0, min(100.0, predicted_score))
    predicted_score = round(predicted_score, 2)
    
    # Logistic sigmoid pass probability
    prob = 1.0 / (1.0 + math.exp(-0.15 * (predicted_score - pass_mark)))
    pass_prob = round(prob * 100.0, 1)
    
    # Suggestions list compiling
    suggestions = []
    if slope > 0.5:
        suggestions.append("Your performance shows a strong positive trend! Keep up the current study schedule.")
    elif slope < -0.5:
        suggestions.append("Score trends are currently declining. We advise pausing tests to practice weak subject areas.")
    else:
        suggestions.append("Your performance is stable. Aim to raise scores on upcoming tests by focusing on harder MCQs.")
        
    if predicted_score < pass_mark:
        suggestions.append("Current prediction falls below passing marks. Review incorrect choices in past attempts.")
        
    return {
        "predicted_score": predicted_score,
        "pass_probability": pass_prob,
        "improvement_rate": round(slope, 2),
        "suggestions": suggestions
    }
