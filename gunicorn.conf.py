"""Gunicorn production configuration for TeleMed Seva."""
import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# ── Workers ───────────────────────────────────────────────────────────────────
# Recommended formula: (2 × CPU cores) + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'   # use 'gevent' if you add gevent to requirements
threads = int(os.getenv('GUNICORN_THREADS', 2))
worker_connections = 1000
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
keepalive = 5

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')   # '-' = stdout
errorlog  = os.getenv('GUNICORN_ERROR_LOG',  '-')
loglevel  = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

# ── Security ──────────────────────────────────────────────────────────────────
limit_request_line   = 4094
limit_request_fields = 100

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = 'telemed_seva'

# ── Hooks ─────────────────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("TeleMed Seva — starting Gunicorn")

def worker_exit(server, worker):
    server.log.info("Worker %s exiting", worker.pid)
