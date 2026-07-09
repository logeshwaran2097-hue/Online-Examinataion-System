-- ============================================================
-- Online Examination System — PostgreSQL Database Setup
-- Run this script as a PostgreSQL superuser (e.g. postgres)
-- ============================================================

-- 1. Create dedicated database user
CREATE USER exam_admin WITH PASSWORD 'your_password';

-- 2. Create the database
CREATE DATABASE online_examination_system
    WITH OWNER      = exam_admin
         ENCODING   = 'UTF8'
         LC_COLLATE = 'en_US.UTF-8'
         LC_CTYPE   = 'en_US.UTF-8'
         TEMPLATE   = template0;

-- 3. Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE online_examination_system TO exam_admin;

-- 4. Connect to the new database and grant schema rights
\c online_examination_system
GRANT ALL ON SCHEMA public TO exam_admin;

-- ── Verification ─────────────────────────────────────────────
-- Run after setup to confirm access:
-- psql -U exam_admin -d online_examination_system -c "\dt"
