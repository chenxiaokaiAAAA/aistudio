#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能图片清理系统快速启动脚本
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """打印横幅"""
    print("🧹 智能图片清理系统")
    print("=" * 50)
    print("基于订单状态的智能图片清理")
    print("发货后10天自动清理高清图片")
    print("支持百度云备份和恢复")
    print("=" * 50)

def run_cleanup():
    """运行清理任务"""
    print(f"🕐 开始执行清理任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        result = subprocess.run([sys.executable, 'smart_image_cleanup.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 清理任务执行成功")
            print(result.stdout)
        else:
            print("❌ 清理任务执行失败")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 执行清理任务异常: {e}")

def run_backup():
    """运行备份任务"""
    print(f"☁️  开始执行备份任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        result = subprocess.run([sys.executable, 'baidu_cloud_backup.py'], 
                              capture_output=True, text=True, input="3\n")
        
        if result.returncode == 0:
            print("✅ 备份任务执行成功")
            print(result.stdout)
        else:
            print("❌ 备份任务执行失败")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 执行备份任务异常: {e}")

def run_full_task():
    """运行完整任务"""
    print(f"🔄 开始执行完整任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 先执行清理
        run_cleanup()
        
        # 再执行备份
        run_backup()
        
        print("✅ 完整任务执行完成")
        
    except Exception as e:
        print(f"❌ 执行完整任务异常: {e}")

def show_status():
    """显示系统状态"""
    print("📊 系统状态检查")
    print("-" * 30)
    
    # 检查文件是否存在
    files_to_check = [
        'smart_image_cleanup.py',
        'baidu_cloud_backup.py', 
        'scheduled_cleanup.py',
        'image_cleanup_log.json',
        'baidu_cloud_config.json'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
    
    # 检查目录
    dirs_to_check = ['hd_images', 'uploads', 'final_works']
    
    print("\n📁 目录检查:")
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) 
                            if os.path.isfile(os.path.join(dir_path, f))])
            print(f"✅ {dir_path}/ ({file_count} 个文件)")
        else:
            print(f"❌ {dir_path}/ (不存在)")

def main():
    """主函数"""
    print_banner()
    
    while True:
        print("\n请选择操作:")
        print("1. 执行清理任务")
        print("2. 执行备份任务") 
        print("3. 执行完整任务（清理+备份）")
        print("4. 查看系统状态")
        print("5. 运行测试")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "1":
            run_cleanup()
        elif choice == "2":
            run_backup()
        elif choice == "3":
            run_full_task()
        elif choice == "4":
            show_status()
        elif choice == "5":
            print("🧪 运行系统测试...")
            try:
                subprocess.run([sys.executable, 'test_cleanup_system.py', '--test'])
            except Exception as e:
                print(f"❌ 测试失败: {e}")
        elif choice == "0":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择")

if __name__ == '__main__':
    main()




