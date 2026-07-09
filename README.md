# Online Examination System (OES)

A secure, scalable, and interactive Online Examination System built using **Python Flask, PostgreSQL, SQLAlchemy, Bootstrap 5, JavaScript, and Chart.js**. This application features AI-based student score predictions, performance diagnostics question recommendations, active webcam proctoring, and digital certificate verify systems.

---

## 🚀 Key Features

1. **Authentication & Authorization**: Role-based access control isolating Admin roles from Student users. Includes verification checks and dynamic OTP mail dispatches.
2. **Proctor-Secured Exam taker**: Hides structural navigation bars. Locks context menus (right-click block) and keyboard copy/paste actions.
3. **Active Webcam Proctoring**: Requests webcam access, captures candidate snapshots every 30 seconds, and posts them to storage.
4. **Anti-Cheating surveillance**: Detects page focus loss (tab switching) and alerts candidates. Exceeding 3 tab switches auto-submits the exam immediately.
5. **AI Score Prediction**: Runs a linear regression progression model over historical grades to forecast scores.
6. **AI Question Recommendation**: Suggests practice questions and core topics checklist matching target difficulty depending on average subject mastery.
7. **Report Exporters**: Allows students and admins to export grades transcripts as Excel (`.xlsx`), CSV text sheets, or ReportLab PDF reports.
8. **QR Verified Certificates**: Pass grades automatically award certificate credentials embedded with public validation QR codes.

---

## 🛠️ Installation & Setup

### Prerequisites
* Python 3.9+
* PostgreSQL 12+ (or SQLite for quick local test runs)
* Virtual Environment manager (`venv`)

### 1. Clone & Setup Virtual Environment
```bash
git clone <repository-url>
cd Online-Examination-System
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=dev-secret-key-12345!
DATABASE_URL=postgresql://postgres:password@localhost:5432/online_examination_system
FLASK_DEBUG=True

# Flask-Mail configurations (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 3. Initialize Databases
To build the tables matching the SQLAlchemy models, you can run our interactive seeding script:
```bash
python scratch/seed_db.py
```
This drops existing tables, configures all schema bounds, and seeds student/admin accounts alongside sample MCQ exams.

### 4. Run Development Server
```bash
flask run
# Web App bounds: http://127.0.0.1:5000
```

---

## 🌐 Production Deployment

### Gunicorn WSGI execution
To start the production server, use Gunicorn:
```bash
gunicorn -c gunicorn.conf.py app:app
# Server starts binding at: http://0.0.0.0:8000
```

### Docker Deployment
Create a `Dockerfile` in the root:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
```
Build and run the container:
```bash
docker build -t oes-app .
docker run -d -p 8000:8000 --env-file .env oes-app
```
