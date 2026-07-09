import io
import csv
import openpyxl
from datetime import datetime
from models import Result, User

def generate_excel_report(student_id):
    """
    Generates a BytesIO Excel spreadsheet of a student's examination history.
    """
    student = User.query.get(student_id)
    results = Result.query.filter_by(student_id=student_id).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Academic Transcripts"
    
    # Write student details
    ws.append(["EduExam Academic Transcript", ""])
    ws.append(["Student Name:", student.full_name if student else "N/A"])
    ws.append(["Email:", student.email if student else "N/A"])
    ws.append(["Date Generated:", datetime.now().strftime('%Y-%m-%d')])
    ws.append([]) # spacer
    
    # Table headers
    ws.append(["Exam Title", "Subject", "Total Marks", "Obtained Marks", "Percentage", "Grade", "Status", "Exam Date"])
    
    for r in results:
        ws.append([
            r.exam.exam_title,
            r.exam.subject_name,
            r.total_marks,
            r.obtained_marks,
            f"{r.percentage}%",
            r.grade,
            r.pass_fail_status.upper(),
            r.generated_at.strftime('%Y-%m-%d')
        ])
        
    # Autofit column width
    for col in ws.columns:
        max_len = max(len(str(val.value or '')) for val in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 10)
        
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out

def generate_csv_report(student_id):
    """
    Generates a BytesIO CSV stream of a student's examination history.
    """
    results = Result.query.filter_by(student_id=student_id).all()
    
    out = io.StringIO()
    writer = csv.writer(out)
    
    writer.writerow(["Exam Title", "Subject", "Total Marks", "Obtained Marks", "Percentage", "Grade", "Status", "Date Taken"])
    for r in results:
        writer.writerow([
            r.exam.exam_title,
            r.exam.subject_name,
            r.total_marks,
            r.obtained_marks,
            f"{r.percentage}%",
            r.grade,
            r.pass_fail_status.upper(),
            r.generated_at.strftime('%Y-%m-%d')
        ])
        
    mem = io.BytesIO(out.getvalue().encode('utf-8'))
    mem.seek(0)
    return mem
