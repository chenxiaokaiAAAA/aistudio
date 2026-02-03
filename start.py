#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI拍照机系统启动脚本
简化版本，只包含必要的启动逻辑
"""

import os
import sys
import hashlib
import time
import random
import string
import requests
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_server import app, db, User
from werkzeug.security import generate_password_hash
from flask import request

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    """主启动函数"""
    logger = setup_logging()
    
    with app.app_context():
        # 在应用上下文中获取品牌名称
        from app.utils.config_loader import get_brand_name
        brand_name = get_brand_name()
        logger.info(f"🚀 启动{brand_name}系统...")
        print(f"🚀 启动{brand_name}系统...")
        try:
            # 创建数据库表
            start_time = time.time()
            db.create_all()
            db_time = time.time() - start_time
            logger.info(f"数据库表创建完成，耗时: {db_time:.2f}秒")
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
                logger.info("创建默认管理员账号: admin/admin123")
                print("✅ 创建默认管理员账号: admin/admin123")
            else:
                logger.info("管理员账号已存在")
                print("✅ 管理员账号已存在")
            
            # 检查是否有风格分类数据
            try:
                from test_server import StyleCategory
                category_count = StyleCategory.query.count()
                if category_count == 0:
                    logger.warning("未检测到风格分类数据，请通过管理后台初始化")
                    print("⚠️  未检测到风格分类数据，请通过管理后台初始化")
                else:
                    logger.info(f"检测到 {category_count} 个风格分类")
                    print(f"✅ 检测到 {category_count} 个风格分类")
            except ImportError:
                logger.warning("风格分类模块未找到")
                print("⚠️  风格分类模块未找到")
            
            # 执行数据库迁移
            try:
                from test_server import migrate_database
                migrate_database()
                logger.info("数据库迁移完成")
                print("✅ 数据库迁移完成")
            except Exception as e:
                logger.warning(f"数据库迁移失败: {str(e)}")
                print(f"⚠️  数据库迁移失败: {str(e)}")
            
            # 初始化默认数据
            try:
                from test_server import init_default_data
                init_default_data()
                logger.info("默认数据初始化完成")
                print("✅ 默认数据初始化完成")
            except Exception as e:
                logger.warning(f"默认数据初始化失败: {str(e)}")
                print(f"⚠️  默认数据初始化失败: {str(e)}")
            
            # 初始化并发配置
            try:
                from test_server import init_concurrency_configs
                init_concurrency_configs()
                logger.info("并发配置初始化完成")
                print("✅ 并发配置初始化完成")
            except Exception as e:
                logger.warning(f"并发配置初始化失败: {str(e)}")
                print(f"⚠️  并发配置初始化失败: {str(e)}")
            
            # 启动任务队列服务
            try:
                from app.services.task_queue_service import start_task_queue
                start_task_queue()
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
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            print(f"❌ 数据库初始化失败: {str(e)}")
            raise
    
    logger.info("启动Web服务器...")
    print("🌐 启动Web服务器...")
    print("📱 小程序API: http://192.168.2.54:8000/api/miniprogram/")
    print("🖥️  管理后台: http://192.168.2.54:8000/admin/")
    print("🌍 网页版: http://192.168.2.54:8000/")
    print("=" * 50)
    
    # 添加请求监控中间件
    @app.before_request
    def log_request():
        logger.info(f"请求: {request.method} {request.url}")
    
    @app.after_request
    def log_response(response):
        logger.info(f"响应: {response.status_code}")
        return response
    
    # 启动Flask应用 - 优化配置解决卡顿问题
    try:
        logger.info("Flask应用启动中...")
        app.run(
            host='0.0.0.0', 
            port=8000, 
            debug=True,  # 开发环境启用debug模式，自动重载模板
            threaded=True,  # 启用多线程支持
            use_reloader=True,  # 启用自动重载
            processes=1  # 单进程多线程
        )
    except Exception as e:
        logger.error(f"Flask应用启动失败: {str(e)}")
        print(f"❌ Flask应用启动失败: {str(e)}")
        raise

if __name__ == '__main__':
    main()

