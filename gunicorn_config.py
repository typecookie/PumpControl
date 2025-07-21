# gunicorn_config.py
import multiprocessing
import os

from jinja2.lexer import TOKEN_DOT

# Server socket settings
bind = "127.0.0.1:8000"
backlog = 2048

# Worker settings
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120  # Increased timeout
keepalive = 2
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# Process naming
proc_name = 'pump-control'

# Logging
accesslog = '/opt/pump-control/logs/access.log'
errorlog = '/opt/pump-control/logs/error.log'
loglevel = 'info'

# Server mechanics
daemon = False
pidfile = 'gunicorn.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

def on_starting(server):
    """Run when the master process is started."""
    print("Starting Gunicorn server...")

def on_exit(server):
    """Run when the master process is stopped."""
    print("Shutting down Gunicorn server...")

def post_fork(server, worker):
    """Run after a worker has been forked."""
    try:
        from app.controllers.pump_controller import PumpController
        
        # Initialize the pump controller in the worker
        controller = PumpController()
        if not controller.is_running:
            controller.start()
        
        print(f"Worker initialized. Current mode: {controller.current_mode}")
    except Exception as e:
        print(f"Error initializing worker: {e}")
        
def worker_exit(server, worker):
    """Run when a worker exits."""
    try:
        from app.controllers.pump_controller import PumpController
        
        # Clean up the pump controller
        controller = PumpController()
        if controller.is_running:
            controller.stop()
        print("Worker shutting down, pump controller stopped.")
    except Exception as e:
        print(f"Error during worker cleanup: {e}")