# gunicorn_config.py
import multiprocessing
import os

# Server socket settings
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1  # For this application, we want only 1 worker due to GPIO handling
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = 'pump-control'

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
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
    from app.controllers.pump_controller import PumpController
    
    # Initialize the pump controller in the worker
    controller = PumpController()
    if not controller.is_running:
        controller.start()
    
    print(f"Worker initialized. Current mode: {controller.current_mode}")

def worker_exit(server, worker):
    """Run when a worker exits."""
    from app.controllers.pump_controller import PumpController
    
    # Clean up the pump controller
    controller = PumpController()
    controller.stop()
    print("Worker shutting down, pump controller stopped.")