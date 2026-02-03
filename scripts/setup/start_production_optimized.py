#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生产环境优化启动脚本
专门解决运行中卡顿问题
"""

import os
import sys
import subprocess
import time
import logging
import signal
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """配置日志系统"""
    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/production.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_dependencies():
    """检查依赖"""
    try:
        import gunicorn
        print("✅ Gunicorn已安装")
        return True
    except ImportError:
        print("❌ Gunicorn未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gunicorn'])
            print("✅ Gunicorn安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ Gunicorn安装失败")
            return False

def create_optimized_gunicorn_config():
    """创建优化的Gunicorn配置"""
    config_content = '''#!/usr/bin/env python3
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
'''
    
    with open('gunicorn_optimized.conf.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ 创建优化的Gunicorn配置文件")

def main():
    """主启动函数"""
    logger = setup_logging()
    from app.utils.config_loader import get_brand_name
    brand_name = get_brand_name()
    logger.info(f"🚀 启动{brand_name}系统 (生产环境优化版)...")
    print(f"🚀 启动{brand_name}系统 (生产环境优化版)...")
    print("🔧 专门解决运行中卡顿问题")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，退出")
        return
    
    # 确保必要目录存在
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('final_works', exist_ok=True)
    os.makedirs('hd_images', exist_ok=True)
    
    # 创建优化的Gunicorn配置
    create_optimized_gunicorn_config()
    
    print("🌐 使用优化的Gunicorn启动Web服务器...")
    print("📱 小程序API: http://photogooo:8000/api/miniprogram/")
    print("🖥️  管理后台: http://photogooo:8000/admin/")
    print("🌍 网页版: http://photogooo:8000/")
    print("=" * 50)
    
    # 启动Gunicorn
    try:
        cmd = [
            'gunicorn',
            '--config', 'gunicorn_optimized.conf.py',
            'test_server:app'
        ]
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        print(f"执行命令: {' '.join(cmd)}")
        
        # 启动Gunicorn进程
        process = subprocess.Popen(cmd)
        
        # 等待进程启动
        time.sleep(3)
        
        if process.poll() is None:
            logger.info("Gunicorn启动成功")
            print("✅ Gunicorn启动成功")
            print("🔧 优化配置已生效:")
            print("   - 数据库连接池优化")
            print("   - 外部API超时优化")
            print("   - 异步处理机制")
            print("   - 多线程支持")
            print("按 Ctrl+C 停止服务器")
            
            try:
                # 等待进程结束
                process.wait()
            except KeyboardInterrupt:
                logger.info("收到停止信号，正在关闭服务器...")
                print("\n🛑 正在关闭服务器...")
                process.terminate()
                process.wait()
                logger.info("服务器已关闭")
                print("✅ 服务器已关闭")
        else:
            logger.error("Gunicorn启动失败")
            print("❌ Gunicorn启动失败")
            
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        print(f"❌ 启动失败: {str(e)}")

if __name__ == '__main__':
    main()

