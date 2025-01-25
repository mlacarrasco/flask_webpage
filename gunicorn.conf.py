import multiprocessing

bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = 1
worker_connections = 1000
max_requests = 0
timeout = 300
keepalive = 2

# Eventlet settings
worker_class = "eventlet"
worker_connections = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# SSL Configuration (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# Process Naming
proc_name = "gunicorn_flask_app"

# Server Mechanics
graceful_timeout = 120
timeout = 300
keepalive = 5