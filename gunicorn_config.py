import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
# Gunicorn's recommendation: (2 x $num_cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Process naming
proc_name = "service-topology-agent" 