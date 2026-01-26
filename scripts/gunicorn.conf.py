#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gunicorn配置文件
用于生产环境部署，解决卡顿问题
"""

import multiprocessing
import os

# 服务器套接字
bind = "0.0.0.0:8000"
backlog = 2048

# Worker进程
workers = multiprocessing.cpu_count() * 2 + 1  # 根据CPU核心数设置
worker_class = "sync"  # 同步worker，适合I/O密集型应用
worker_connections = 1000
timeout = 30
keepalive = 2

# 重启
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
pidfile = "gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (如果需要)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# 环境变量
raw_env = [
    'FLASK_ENV=production',
]

def when_ready(server):
    """服务器启动完成时的回调"""
    server.log.info("服务器启动完成，开始接受连接")

def worker_int(worker):
    """Worker进程中断时的回调"""
    worker.log.info("Worker进程被中断")

def pre_fork(server, worker):
    """Fork worker进程前的回调"""
    server.log.info("准备启动Worker进程")

def post_fork(server, worker):
    """Fork worker进程后的回调"""
    server.log.info(f"Worker进程 {worker.pid} 启动完成")