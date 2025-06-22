"""
Gunicorn 配置文件
使用统一的配置管理器管理所有Gunicorn相关配置。
"""

import multiprocessing
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import ConfigManager

# 加载配置
config = ConfigManager()

# 获取Gunicorn配置
gunicorn_config = config.get_section('gunicorn')

# Server socket
bind = gunicorn_config['bind']

# Worker processes
workers = gunicorn_config['workers']
worker_class = gunicorn_config['worker_class']

# Timeout settings
timeout = gunicorn_config['timeout']
keepalive = gunicorn_config['keepalive']

# Request limits
max_requests = gunicorn_config['max_requests']
max_requests_jitter = gunicorn_config['max_requests_jitter']

# Logging
accesslog = gunicorn_config['accesslog']
errorlog = gunicorn_config['errorlog']
loglevel = gunicorn_config['loglevel']

# Process naming
proc_name = gunicorn_config['proc_name']

# Additional settings
preload_app = True
worker_connections = 1000
max_requests_jitter = 100

# SSL settings (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Security settings
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190 