#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生产环境启动脚本
使用Gunicorn启动Flask应用，适用于Linux生产环境部署
"""

import os
import sys
import subprocess
import time
import logging
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
            logging.FileHandler('logs/startup.log', encoding='utf-8'),
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

def init_database():
    """初始化数据库"""
    try:
        from test_server import app, db, User
        from werkzeug.security import generate_password_hash
        
        with app.app_context():
            # 创建数据库表
            db.create_all()
            print("✅ 数据库表创建完成")
            
            # 检查并创建默认管理员账号
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ 创建默认管理员账号: admin/admin123")
            else:
                print("✅ 管理员账号已存在")
            
            # 执行数据库迁移
            try:
                from test_server import migrate_database
                migrate_database()
                print("✅ 数据库迁移完成")
            except Exception as e:
                print(f"⚠️  数据库迁移失败: {str(e)}")
            
            # 初始化默认数据
            try:
                from test_server import init_default_data
                init_default_data()
                print("✅ 默认数据初始化完成")
            except Exception as e:
                print(f"⚠️  默认数据初始化失败: {str(e)}")
            
            # 初始化并发配置
            try:
                from test_server import init_concurrency_configs
                init_concurrency_configs()
                print("✅ 并发配置初始化完成")
            except Exception as e:
                print(f"⚠️  并发配置初始化失败: {str(e)}")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        raise

def main():
    """主启动函数"""
    logger = setup_logging()
    
    # 获取品牌名称
    try:
        from app.utils.config_loader import get_brand_name
        brand_name = get_brand_name()
    except:
        brand_name = 'AI拍照机'
    
    logger.info(f"🚀 启动{brand_name}系统 (生产环境)...")
    print(f"🚀 启动{brand_name}系统 (生产环境)...")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，退出")
        return
    
    # 确保必要目录存在
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('final_works', exist_ok=True)
    os.makedirs('hd_images', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        print(f"❌ 数据库初始化失败: {str(e)}")
        return
    
    # 启动任务队列服务（在后台线程中）
    try:
        from app.services.task_queue_service import start_task_queue
        import threading
        queue_thread = threading.Thread(target=start_task_queue, daemon=True)
        queue_thread.start()
        logger.info("任务队列服务已启动")
        print("✅ 任务队列服务已启动")
    except Exception as e:
        logger.warning(f"启动任务队列服务失败: {str(e)}")
        print(f"⚠️  启动任务队列服务失败: {str(e)}")
    
    # 启动AI任务状态自动轮询服务
    try:
        from app.services.ai_task_polling_service import init_ai_task_polling_service
        init_ai_task_polling_service()
        logger.info("AI任务状态自动轮询服务已启动")
        print("✅ AI任务状态自动轮询服务已启动")
    except Exception as e:
        logger.warning(f"启动AI任务状态轮询服务失败: {str(e)}")
        print(f"⚠️  启动AI任务状态轮询服务失败: {str(e)}")
    
    # 检查Gunicorn配置文件
    gunicorn_config = 'gunicorn.conf.py'
    if not os.path.exists(gunicorn_config):
        # 如果根目录没有，检查scripts目录
        if os.path.exists(os.path.join('scripts', gunicorn_config)):
            gunicorn_config = os.path.join('scripts', gunicorn_config)
        else:
            print(f"⚠️  未找到Gunicorn配置文件，使用默认配置")
            gunicorn_config = None
    
    print("🌐 使用Gunicorn启动Web服务器...")
    print("=" * 50)
    
    # 启动Gunicorn
    try:
        cmd = ['gunicorn', 'test_server:app']
        
        if gunicorn_config:
            cmd.extend(['--config', gunicorn_config])
        else:
            # 使用命令行参数
            import multiprocessing
            cmd.extend([
                '--bind', '0.0.0.0:8000',
                '--workers', str(multiprocessing.cpu_count() * 2 + 1),
                '--worker-class', 'sync',
                '--timeout', '30',
                '--access-logfile', 'logs/access.log',
                '--error-logfile', 'logs/error.log',
                '--log-level', 'info',
                '--pid', 'gunicorn.pid'
            ])
        
        logger.info(f"执行命令: {' '.join(cmd)}")
        print(f"执行命令: {' '.join(cmd)}")
        
        # 启动Gunicorn进程
        process = subprocess.Popen(cmd)
        
        # 等待进程启动
        time.sleep(2)
        
        if process.poll() is None:
            logger.info("Gunicorn启动成功")
            print("✅ Gunicorn启动成功")
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
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
