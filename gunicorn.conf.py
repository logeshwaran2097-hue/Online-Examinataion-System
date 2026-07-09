import multiprocessing

# Gunicorn configuration file for production deployment
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
timeout = 120
keepalive = 5

# Logging settings
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process management
proc_name = "online_examination_system"
daemon = False
