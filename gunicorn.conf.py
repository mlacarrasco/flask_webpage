import multiprocessing

bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = 1
threads = 1000
worker_connections = 1000
max_requests = 0
timeout = 300
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'