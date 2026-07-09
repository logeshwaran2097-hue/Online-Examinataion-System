-- PostgreSQL Database DDL for Online Examination System
-- Professional, Scalable, Secure, and Normalized Schema

-- Drop existing tables to ensure clean setup (if needed, in order of dependencies)
DROP TABLE IF EXISTS certificates CASCADE;
DROP TABLE IF EXISTS exam_monitoring CASCADE;
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS otp_verification CASCADE;
DROP TABLE IF EXISTS results CASCADE;
DROP TABLE IF EXISTS student_answers CASCADE;
DROP TABLE IF EXISTS options CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS leaderboard CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create shared updated_at auto-refresh function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- 1. users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(15) UNIQUE,
    password VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    year_of_study INTEGER,
    profile_image TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_year_of_study CHECK (year_of_study BETWEEN 1 AND 8)
);

CREATE TRIGGER trigger_update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- 2. admins
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) DEFAULT 'admin',
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 3. exams
CREATE TABLE exams (
    id SERIAL PRIMARY KEY,
    exam_title VARCHAR(150) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_minutes INTEGER NOT NULL,
    total_questions INTEGER DEFAULT 0,
    total_marks INTEGER DEFAULT 0,
    pass_mark INTEGER DEFAULT 0,
    exam_date DATE,
    start_time TIME,
    end_time TIME,
    status VARCHAR(20) DEFAULT 'upcoming',
    created_by INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_exam_duration CHECK (duration_minutes > 0),
    CONSTRAINT chk_exam_questions CHECK (total_questions >= 0),
    CONSTRAINT chk_exam_total_marks CHECK (total_marks >= 0),
    CONSTRAINT chk_exam_pass_mark CHECK (pass_mark >= 0 AND pass_mark <= total_marks),
    CONSTRAINT chk_exam_status CHECK (status IN ('upcoming', 'ongoing', 'completed', 'cancelled'))
);

CREATE TRIGGER trigger_update_exams_updated_at
BEFORE UPDATE ON exams
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- 4. questions
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(30),
    difficulty_level VARCHAR(20),
    marks INTEGER DEFAULT 1,
    correct_answer VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_question_marks CHECK (marks > 0),
    CONSTRAINT chk_question_type CHECK (question_type IN ('mcq', 'true_false', 'subjective')),
    CONSTRAINT chk_question_difficulty CHECK (difficulty_level IN ('easy', 'medium', 'hard'))
);

CREATE TRIGGER trigger_update_questions_updated_at
BEFORE UPDATE ON questions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- 5. options
CREATE TABLE options (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE UNIQUE,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT
);


-- 6. student_answers
CREATE TABLE student_answers (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    selected_answer VARCHAR(10),
    answer_status BOOLEAN,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 7. results
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    total_marks INTEGER,
    obtained_marks INTEGER,
    percentage DECIMAL(5,2),
    grade VARCHAR(10),
    pass_fail_status VARCHAR(10),
    rank INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_result_marks CHECK (obtained_marks >= 0 AND obtained_marks <= total_marks),
    CONSTRAINT chk_result_percentage CHECK (percentage BETWEEN 0.00 AND 100.00),
    CONSTRAINT chk_result_pass_status CHECK (pass_fail_status IN ('pass', 'fail'))
);


-- 8. otp_verification
CREATE TABLE otp_verification (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100),
    otp VARCHAR(10),
    expiry_time TIMESTAMP,
    verification_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 9. notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    message TEXT,
    notification_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 10. attendance
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    login_time TIMESTAMP,
    logout_time TIMESTAMP,
    attendance_status VARCHAR(20),
    CONSTRAINT chk_attendance_status CHECK (attendance_status IN ('present', 'absent', 'late', 'suspended')),
    CONSTRAINT chk_attendance_logout CHECK (logout_time IS NULL OR logout_time >= login_time)
);


-- 11. activity_logs
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    user_role VARCHAR(20),
    activity TEXT,
    ip_address VARCHAR(50),
    browser VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 12. exam_monitoring
CREATE TABLE exam_monitoring (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    tab_switch_count INTEGER DEFAULT 0,
    webcam_status BOOLEAN DEFAULT TRUE,
    suspicious_activity TEXT,
    captured_image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tab_switch CHECK (tab_switch_count >= 0)
);


-- 13. certificates
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    certificate_number VARCHAR(100) UNIQUE NOT NULL,
    qr_code TEXT,
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 14. leaderboard
CREATE TABLE leaderboard (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    total_score INTEGER DEFAULT 0,
    rank_position INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_total_score CHECK (total_score >= 0),
    CONSTRAINT chk_rank_position CHECK (rank_position > 0)
);

CREATE TRIGGER trigger_update_leaderboard_updated_at
BEFORE UPDATE ON leaderboard
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- 15. analytics
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subject_name VARCHAR(100) NOT NULL,
    average_score DECIMAL(5,2) DEFAULT 0.00,
    exams_taken INTEGER DEFAULT 0,
    performance_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_avg_score CHECK (average_score BETWEEN 0.00 AND 100.00),
    CONSTRAINT chk_exams_taken CHECK (exams_taken >= 0)
);


-- PostgreSQL Indexes for Performance Optimization
-- B-Tree indexes are created explicitly on all foreign keys to optimize joins and filters

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_admins_username ON admins(username);
CREATE INDEX idx_exams_created_by ON exams(created_by);
CREATE INDEX idx_exams_status ON exams(status);
CREATE INDEX idx_exams_date ON exams(exam_date);
CREATE INDEX idx_questions_exam_id ON questions(exam_id);
CREATE INDEX idx_options_question_id ON options(question_id);
CREATE INDEX idx_student_answers_student ON student_answers(student_id);
CREATE INDEX idx_student_answers_exam ON student_answers(exam_id);
CREATE INDEX idx_student_answers_question ON student_answers(question_id);
CREATE INDEX idx_results_student ON results(student_id);
CREATE INDEX idx_results_exam ON results(exam_id);
CREATE INDEX idx_otp_verification_email ON otp_verification(email);
CREATE INDEX idx_notifications_user_is_read ON notifications(user_id, is_read);
CREATE INDEX idx_attendance_student_exam ON attendance(student_id, exam_id);
CREATE INDEX idx_exam_monitoring_student_exam ON exam_monitoring(student_id, exam_id);
CREATE INDEX idx_certificates_student_exam ON certificates(student_id, exam_id);
CREATE INDEX idx_leaderboard_rank ON leaderboard(rank_position);
CREATE INDEX idx_analytics_student ON analytics(student_id);
