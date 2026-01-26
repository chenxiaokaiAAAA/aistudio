#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化的Gunicorn配置文件
专门解决运行中卡顿问题
"""

import multiprocessing
import os

# 服务器套接字
bind = "0.0.0.0:8000"
backlog = 2048

# Worker进程 - 优化配置
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60  # 增加超时时间
keepalive = 5  # 增加keepalive时间
max_requests = 500  # 减少最大请求数，定期重启worker
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

# 环境变量
raw_env = [
    'FLASK_ENV=production',
    'PYTHONUNBUFFERED=1',  # 确保日志实时输出
]

def when_ready(server):
    """服务器启动完成时的回调"""
    server.log.info("🚀 生产环境服务器启动完成，开始接受连接")
    print("🚀 生产环境服务器启动完成")

def worker_int(worker):
    """Worker进程中断时的回调"""
    server.log.info(f"Worker进程 {worker.pid} 被中断")

def pre_fork(server, worker):
    """Fork worker进程前的回调"""
    server.log.info(f"准备启动Worker进程 {worker.age}")

def post_fork(server, worker):
    """Fork worker进程后的回调"""
    server.log.info(f"Worker进程 {worker.pid} 启动完成")

def worker_abort(worker):
    """Worker进程异常退出时的回调"""
    server.log.info(f"Worker进程 {worker.pid} 异常退出")
