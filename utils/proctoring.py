import os
import base64
import uuid
from datetime import datetime
from database import db
from models import ExamMonitoring

def save_proctoring_snapshot(student_id, exam_id, base64_image_data):
    """
    Decodes a base64 webcam snapshot and saves it as a file inside the
    static/uploads/proctoring/ directory.
    Returns: The relative web-accessible filepath to the saved image.
    """
    if not base64_image_data:
        return None
        
    try:
        # Strip headers if present
        if "," in base64_image_data:
            header, base64_image_data = base64_image_data.split(",", 1)
            
        img_bytes = base64.b64decode(base64_image_data)
        
        # Setup uploads directory
        upload_dir = os.path.join("static", "uploads", "proctoring")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save snapshot
        filename = f"proctor_{student_id}_{exam_id}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(img_bytes)
            
        # Returns relative url like: /static/uploads/proctoring/filename.png
        relative_path = f"/static/uploads/proctoring/{filename}"
        return relative_path
    except Exception as e:
        print(f"Error saving proctoring image: {e}")
        return None

def update_proctoring_violation(student_id, exam_id, violation_text):
    """
    Appends a new suspicious activity entry and increments warnings.
    """
    monitor = ExamMonitoring.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if not monitor:
        monitor = ExamMonitoring(
            student_id=student_id,
            exam_id=exam_id,
            tab_switch_count=0,
            suspicious_activity=""
        )
        db.session.add(monitor)
        
    timestamp = datetime.now().strftime('%H:%M:%S')
    new_log = f"[{timestamp}] {violation_text}"
    
    if monitor.suspicious_activity:
        monitor.suspicious_activity += f"\n{new_log}"
    else:
        monitor.suspicious_activity = new_log
        
    db.session.commit()
    return monitor
