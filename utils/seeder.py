import random
from datetime import datetime, date, time, timedelta
from database import db, bcrypt
from models import User, Admin, Exam, Attendance, Question, Option, StudentAnswer, Result, Certificate, ExamMonitoring, Notification, ActivityLog, Leaderboard, Analytics

def seed_demo_data():
    """
    Seeds the database with high-quality mock data for demo purposes.
    Only seeds if the database is currently empty of exams/students.
    """
    try:
        # Check if already seeded
        if Exam.query.first() is not None:
            return

        # 1. Seed Admins
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                email='admin@eduexam.com',
                password=bcrypt.generate_password_hash('adminpassword').decode('utf-8'),
                role='admin'
            )
            db.session.add(admin)
            db.session.flush()

        # 2. Seed Students
        student_data = [
            ('Demo Student', 'student@eduexam.com', 'CS', 3, '+1234567890'),
            ('Alice Smith', 'alice@eduexam.com', 'CS', 3, '+1234567891'),
            ('Bob Johnson', 'bob@eduexam.com', 'IT', 2, '+1234567892'),
            ('Charlie Brown', 'charlie@eduexam.com', 'CS', 1, '+1234567893'),
            ('Diana Prince', 'diana@eduexam.com', 'ECE', 4, '+1234567894')
        ]

        students = []
        for name, email, dept, year, phone in student_data:
            stud = User.query.filter_by(email=email).first()
            if not stud:
                stud = User(
                    full_name=name,
                    email=email,
                    password=bcrypt.generate_password_hash('studentpassword').decode('utf-8'),
                    department=dept,
                    year_of_study=year,
                    phone_number=phone,
                    is_verified=True,
                    status=True
                )
                db.session.add(stud)
            students.append(stud)
        db.session.flush()

        # 3. Seed Exams
        exam1 = Exam(
            exam_title='Data Structures Midterm',
            subject_name='Computer Science',
            description='Midterm exam covering Linked Lists, Stacks, Queues, Trees, and Sorting Algorithms.',
            duration_minutes=60,
            total_questions=5,
            total_marks=5,
            pass_mark=3,
            exam_date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status='completed',
            created_by=admin.id
        )
        exam2 = Exam(
            exam_title='Python Programming Quiz',
            subject_name='Computer Science',
            description='Short assessment testing basic syntax, loops, lists, dicts, and functions.',
            duration_minutes=30,
            total_questions=3,
            total_marks=3,
            pass_mark=2,
            exam_date=date.today(),
            start_time=time(9, 0),
            end_time=time(18, 0),
            status='ongoing',
            created_by=admin.id
        )
        exam3 = Exam(
            exam_title='Database Management Final',
            subject_name='Computer Science',
            description='Comprehensive final exam focusing on Normalization, SQL queries, Indexing, and Transactions.',
            duration_minutes=90,
            total_questions=10,
            total_marks=10,
            pass_mark=5,
            exam_date=date.today() + timedelta(days=3),
            start_time=time(14, 0),
            end_time=time(15, 30),
            status='upcoming',
            created_by=admin.id
        )

        db.session.add_all([exam1, exam2, exam3])
        db.session.flush()

        # 4. Seed Questions & Options for Exam 1 (Data Structures)
        q1_data = [
            ("Which data structure uses the LIFO (Last In First Out) principle?", "Stack", "Queue", "Linked List", "Array", "A"),
            ("What is the worst-case time complexity of Quick Sort?", "O(n log n)", "O(n^2)", "O(n)", "O(log n)", "B"),
            ("Which of the following traversal methods is post-order?", "Root-Left-Right", "Left-Root-Right", "Left-Right-Root", "Right-Left-Root", "C"),
            ("A queue is a: ", "FIFO structure", "LIFO structure", "LILO structure", "FILO structure", "A"),
            ("Which tree traversal visits the nodes in ascending sorted order in a Binary Search Tree?", "Pre-order", "Post-order", "In-order", "Level-order", "C")
        ]

        for i, (txt, a, b, c, d, correct) in enumerate(q1_data):
            q = Question(
                exam_id=exam1.id,
                question_text=txt,
                question_type='mcq',
                difficulty_level='medium',
                marks=1,
                correct_answer=correct
            )
            db.session.add(q)
            db.session.flush()
            opt = Option(
                question_id=q.id,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d
            )
            db.session.add(opt)

        # Questions & Options for Exam 2 (Python Programming)
        q2_data = [
            ("What is the output of len([1, 2, 3]) in Python?", "2", "3", "4", "Error", "B"),
            ("Which keyword is used to define functions in Python?", "func", "def", "function", "lambda", "B"),
            ("What data structure is defined by curly braces {} in Python?", "List", "Set", "Dictionary", "Tuple", "C")
        ]

        for i, (txt, a, b, c, d, correct) in enumerate(q2_data):
            q = Question(
                exam_id=exam2.id,
                question_text=txt,
                question_type='mcq',
                difficulty_level='easy',
                marks=1,
                correct_answer=correct
            )
            db.session.add(q)
            db.session.flush()
            opt = Option(
                question_id=q.id,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d
            )
            db.session.add(opt)

        db.session.flush()

        # 5. Seed Attendance
        attendance_records = []
        # All students present for Exam 1
        for stud in students:
            attendance_records.append(Attendance(
                student_id=stud.id,
                exam_id=exam1.id,
                login_time=datetime.utcnow() - timedelta(days=1, hours=2),
                logout_time=datetime.utcnow() - timedelta(days=1, hours=1),
                attendance_status='present'
            ))

        # Some students present/absent for Exam 2
        attendance_records.append(Attendance(
            student_id=students[0].id, # Demo Student
            exam_id=exam2.id,
            login_time=datetime.utcnow() - timedelta(minutes=15),
            attendance_status='present'
        ))
        attendance_records.append(Attendance(
            student_id=students[1].id, # Alice
            exam_id=exam2.id,
            login_time=datetime.utcnow() - timedelta(minutes=10),
            attendance_status='present'
        ))
        attendance_records.append(Attendance(
            student_id=students[2].id, # Bob
            exam_id=exam2.id,
            attendance_status='absent'
        ))

        db.session.add_all(attendance_records)
        db.session.flush()

        # 6. Seed Results & Certificates for Exam 1
        # Demo Student: 4/5 (Pass)
        r_demo = Result(
            student_id=students[0].id,
            exam_id=exam1.id,
            total_marks=5,
            obtained_marks=4,
            percentage=80.00,
            grade='B',
            pass_fail_status='pass',
            rank=2,
            generated_at=datetime.utcnow() - timedelta(days=1)
        )
        # Alice: 5/5 (Pass)
        r_alice = Result(
            student_id=students[1].id,
            exam_id=exam1.id,
            total_marks=5,
            obtained_marks=5,
            percentage=100.00,
            grade='A',
            pass_fail_status='pass',
            rank=1,
            generated_at=datetime.utcnow() - timedelta(days=1)
        )
        # Charlie: 2/5 (Fail)
        r_charlie = Result(
            student_id=students[3].id,
            exam_id=exam1.id,
            total_marks=5,
            obtained_marks=2,
            percentage=40.00,
            grade='F',
            pass_fail_status='fail',
            rank=4,
            generated_at=datetime.utcnow() - timedelta(days=1)
        )
        # Diana: 3/5 (Pass)
        r_diana = Result(
            student_id=students[4].id,
            exam_id=exam1.id,
            total_marks=5,
            obtained_marks=3,
            percentage=60.00,
            grade='C',
            pass_fail_status='pass',
            rank=3,
            generated_at=datetime.utcnow() - timedelta(days=1)
        )

        db.session.add_all([r_demo, r_alice, r_charlie, r_diana])
        db.session.flush()

        # Add Certificates
        cert1 = Certificate(
            student_id=students[0].id,
            exam_id=exam1.id,
            certificate_number="CERT-DS-2026-0001",
            generated_date=datetime.utcnow() - timedelta(days=1)
        )
        cert2 = Certificate(
            student_id=students[1].id,
            exam_id=exam1.id,
            certificate_number="CERT-DS-2026-0002",
            generated_date=datetime.utcnow() - timedelta(days=1)
        )
        cert3 = Certificate(
            student_id=students[4].id,
            exam_id=exam1.id,
            certificate_number="CERT-DS-2026-0003",
            generated_date=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add_all([cert1, cert2, cert3])

        # 7. Seed Exam Monitoring Logs (Proctoring)
        mon1 = ExamMonitoring(
            student_id=students[0].id,
            exam_id=exam2.id,
            tab_switch_count=0,
            webcam_status=True,
            suspicious_activity=None
        )
        mon2 = ExamMonitoring(
            student_id=students[1].id,
            exam_id=exam2.id,
            tab_switch_count=3,
            webcam_status=True,
            suspicious_activity="Switched browser tab multiple times."
        )
        db.session.add_all([mon1, mon2])

        # 8. Seed Notifications
        notif1 = Notification(
            user_id=students[0].id,
            title="Welcome to EduExam",
            message="Your student profile has been set up successfully. Explore available exams in your dashboard.",
            notification_type="system",
            is_read=True
        )
        notif2 = Notification(
            user_id=students[0].id,
            title="Certificate Issued",
            message="Congratulations! Your completion certificate for 'Data Structures Midterm' has been generated.",
            notification_type="achievement",
            is_read=False
        )
        db.session.add_all([notif1, notif2])

        # 9. Seed Audit/Security Logs
        log1 = ActivityLog(
            user_id=admin.id,
            user_role='admin',
            activity="Created Exam Template 'Database Management Final'",
            ip_address="127.0.0.1",
            browser="Chrome/124.0.0"
        )
        log2 = ActivityLog(
            user_id=students[0].id,
            user_role='student',
            activity="Started assessment: 'Python Programming Quiz'",
            ip_address="127.0.0.1",
            browser="Chrome/124.0.0"
        )
        db.session.add_all([log1, log2])

        # 10. Seed Leaderboard
        l1 = Leaderboard(student_id=students[0].id, total_score=85, rank_position=2)
        l2 = Leaderboard(student_id=students[1].id, total_score=98, rank_position=1)
        l3 = Leaderboard(student_id=students[2].id, total_score=75, rank_position=4)
        l4 = Leaderboard(student_id=students[3].id, total_score=40, rank_position=5)
        l5 = Leaderboard(student_id=students[4].id, total_score=80, rank_position=3)
        db.session.add_all([l1, l2, l3, l4, l5])

        # 11. Seed Analytics
        a1 = Analytics(student_id=students[0].id, subject_name="Computer Science", average_score=82.50, exams_taken=4, performance_level="Excellent")
        a2 = Analytics(student_id=students[0].id, subject_name="Mathematics", average_score=74.00, exams_taken=2, performance_level="Good")
        a3 = Analytics(student_id=students[1].id, subject_name="Computer Science", average_score=96.00, exams_taken=5, performance_level="Outstanding")
        a4 = Analytics(student_id=students[2].id, subject_name="Computer Science", average_score=68.00, exams_taken=3, performance_level="Satisfactory")
        db.session.add_all([a1, a2, a3, a4])

        # Commit everything
        db.session.commit()
        print("INFO: Successfully seeded complete demo datasets.")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding demo data: {e}")
