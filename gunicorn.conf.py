# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 3  # Recommended formula: 2 * num_cores + 1
worker_class = "gevent"  # Changed from "gfile" to "gevent"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
worker_tmp_dir = "/dev/shm"
log_file = "/app/logs/gunicorn.log"
access_log_file = "/app/logs/access.log"
error_log_file = "/app/logs/error.log"
capture_output = True
loglevel = "info"
