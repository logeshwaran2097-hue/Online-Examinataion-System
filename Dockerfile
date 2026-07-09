# ---- Base Image ----
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for psycopg2, Pillow, qrcode)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Gunicorn port
EXPOSE 8000

# Create upload directories
RUN mkdir -p static/uploads/proctoring static/uploads/profiles

# Environment variable defaults (override via --env-file or -e flags)
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Start Gunicorn production server
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
