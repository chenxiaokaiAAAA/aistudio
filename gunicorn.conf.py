#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gunicorn配置文件 - 生产环境
适用于Linux生产环境部署
"""

import multiprocessing
import os

# 服务器套接字
bind = "0.0.0.0:8000"
backlog = 2048

# Worker进程
# 根据CPU核心数设置，Linux生产环境建议使用 2 * CPU核心数 + 1
cpu_count = multiprocessing.cpu_count()
workers = cpu_count * 2 + 1
worker_class = "sync"  # 同步worker，适合I/O密集型应用
worker_connections = 1000
timeout = 120  # 增加超时时间，适应AI任务处理
keepalive = 5

# 重启策略（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50
preload_app = True  # 预加载应用，提高性能

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
# 同时输出到标准输出（可以通过 journalctl 查看）
capture_output = True
enable_stdio_inheritance = True

# 进程管理
pidfile = "gunicorn.pid"
# Linux生产环境建议设置user和group
# user = "www-data"
# group = "www-data"
daemon = False  # 不使用守护进程模式，由systemd管理

# 环境变量
raw_env = [
    'FLASK_ENV=production',
    'SERVER_ENV=production',
]

def when_ready(server):
    """服务器启动完成时的回调"""
    server.log.info("=" * 50)
    server.log.info("🚀 Gunicorn服务器启动完成，开始接受连接")
    server.log.info(f"📊 Worker进程数: {workers}")
    server.log.info(f"💻 CPU核心数: {cpu_count}")
    server.log.info(f"🌐 监听地址: {bind}")
    server.log.info("=" * 50)

def worker_int(worker):
    """Worker进程中断时的回调"""
    worker.log.info(f"Worker进程 {worker.pid} 被中断")

def pre_fork(server, worker):
    """Fork worker进程前的回调"""
    server.log.info(f"准备启动Worker进程 {worker.pid}")

def post_fork(server, worker):
    """Fork worker进程后的回调"""
    server.log.info(f"✅ Worker进程 {worker.pid} 启动完成")

def on_exit(server):
    """服务器退出时的回调"""
    server.log.info("🛑 Gunicorn服务器正在关闭")
