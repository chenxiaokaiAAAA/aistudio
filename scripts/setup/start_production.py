#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生产环境启动脚本
使用Gunicorn启动，解决卡顿问题
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

def main():
    """主启动函数"""
    logger = setup_logging()
    from app.utils.config_loader import get_brand_name
    brand_name = get_brand_name()
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
    
    print("🌐 使用Gunicorn启动Web服务器...")
    print("📱 小程序API: http://photogooo:8000/api/miniprogram/")
    print("🖥️  管理后台: http://photogooo:8000/admin/")
    print("🌍 网页版: http://photogooo:8000/")
    print("=" * 50)
    
    # 启动Gunicorn
    try:
        cmd = [
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            'test_server:app'
        ]
        
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

if __name__ == '__main__':
    main()

