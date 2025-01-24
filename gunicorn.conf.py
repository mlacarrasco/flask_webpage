# gunicorn.conf.py
import multiprocessing

# Server socket
#bind = "0.0.0.0:8000"
#backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Specify path to your WSGI file
wsgi_app = 'wsgi:application'

# Process naming
proc_name = 'gunicorn_flask_app'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Environment
raw_env = [
    'FLASK_APP=app.flask_app',
    'FLASK_ENV=production'
]

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (optional)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'