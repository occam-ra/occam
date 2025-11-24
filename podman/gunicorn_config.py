# Gunicorn configuration for OCCAM Flask container

import multiprocessing
import os

# Server socket
bind = '0.0.0.0:5000'
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '/var/www/occam/logs/gunicorn-access.log'
errorlog = '/var/www/occam/logs/gunicorn-error.log'
loglevel = os.environ.get('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'occam-gunicorn'

# Server mechanics
daemon = False
user = 'occam'
group = 'occam'
umask = 0o002

# Reload on code changes (disable in production)
reload = os.environ.get('GUNICORN_RELOAD', 'false').lower() == 'true'
