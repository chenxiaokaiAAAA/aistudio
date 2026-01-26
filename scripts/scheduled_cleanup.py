#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定时图片清理任务
支持Windows任务计划程序和Linux cron的定时清理
"""

import os
import sys
import json
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from smart_image_cleanup import SmartImageCleanup
    SMART_CLEANUP_AVAILABLE = True
except ImportError:
    SMART_CLEANUP_AVAILABLE = False
    print("警告: smart_image_cleanup模块未找到")

try:
    from baidu_cloud_backup import BaiduCloudBackup
    BAIDU_BACKUP_AVAILABLE = True
except ImportError:
    BAIDU_BACKUP_AVAILABLE = False
    print("警告: baidu_cloud_backup模块未找到")

from cleanup_old_uploaded_images import cleanup_old_uploaded_images
from cleanup_old_final_images import cleanup_old_final_images

class ScheduledCleanupTask:
    """定时清理任务管理器"""
    
    def __init__(self):
        if SMART_CLEANUP_AVAILABLE:
            self.cleanup = SmartImageCleanup()
        else:
            self.cleanup = None
        if BAIDU_BACKUP_AVAILABLE:
            self.backup = BaiduCloudBackup()
        else:
            self.backup = None
        self.task_log_file = 'cleanup_task_log.json'
        
    def load_task_log(self):
        """加载任务日志"""
        if os.path.exists(self.task_log_file):
            try:
                with open(self.task_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载任务日志失败: {e}")
        return []
    
    def save_task_log(self, log_entry):
        """保存任务日志"""
        try:
            task_log = self.load_task_log()
            task_log.append(log_entry)
            
            # 只保留最近30天的日志
            cutoff_date = datetime.now() - timedelta(days=30)
            task_log = [log for log in task_log 
                       if datetime.fromisoformat(log['timestamp']) > cutoff_date]
            
            with open(self.task_log_file, 'w', encoding='utf-8') as f:
                json.dump(task_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务日志失败: {e}")
    
    def run_cleanup_task(self):
        """执行清理任务"""
        print(f"🕐 开始执行定时清理任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'cleanup',
            'status': 'started',
            'details': {}
        }
        
        try:
            # 执行图片清理
            cleaned_count = self.cleanup.cleanup_hd_images_by_order_status()
            
            log_entry['details']['cleaned_count'] = cleaned_count
            log_entry['status'] = 'completed'
            
            print(f"✅ 清理任务完成，清理了 {cleaned_count} 个订单的高清图片")
            
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['details']['error'] = str(e)
            print(f"❌ 清理任务失败: {e}")
        
        # 保存日志
        self.save_task_log(log_entry)
    
    def run_backup_task(self):
        """执行备份任务"""
        print(f"☁️  开始执行定时备份任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'backup',
            'status': 'started',
            'details': {}
        }
        
        try:
            # 执行备份
            backed_up_count = self.backup.backup_cleaned_images()
            
            log_entry['details']['backed_up_count'] = backed_up_count
            log_entry['status'] = 'completed'
            
            print(f"✅ 备份任务完成，备份了 {backed_up_count} 个文件")
            
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['details']['error'] = str(e)
            print(f"❌ 备份任务失败: {e}")
        
        # 保存日志
        self.save_task_log(log_entry)
    
    def run_full_task(self):
        """执行完整任务（清理+备份）"""
        print(f"🔄 开始执行完整任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'full',
            'status': 'started',
            'details': {}
        }
        
        try:
            # 1. 执行清理
            cleaned_count = self.cleanup.cleanup_hd_images_by_order_status()
            log_entry['details']['cleaned_count'] = cleaned_count
            
            # 2. 执行备份
            backed_up_count = self.backup.backup_cleaned_images()
            log_entry['details']['backed_up_count'] = backed_up_count
            
            log_entry['status'] = 'completed'
            
            print(f"✅ 完整任务完成:")
            print(f"   - 清理了 {cleaned_count} 个订单的高清图片")
            print(f"   - 备份了 {backed_up_count} 个文件")
            
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['details']['error'] = str(e)
            print(f"❌ 完整任务失败: {e}")
        
        # 保存日志
        self.save_task_log(log_entry)
    
    def run_uploaded_images_cleanup(self):
        """执行用户上传原图清理任务"""
        print(f"🗑️  开始执行用户上传原图清理任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'uploaded_images_cleanup',
            'status': 'started',
            'details': {}
        }
        
        try:
            # 执行清理（已发货订单，1个月以前）
            cleanup_old_uploaded_images(dry_run=False, days=30)
            log_entry['status'] = 'completed'
            print(f"✅ 用户上传原图清理任务完成")
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['details']['error'] = str(e)
            print(f"❌ 用户上传原图清理任务失败: {e}")
        
        # 保存日志
        self.save_task_log(log_entry)
    
    def run_final_images_cleanup(self):
        """执行效果图清理任务"""
        print(f"🗑️  开始执行效果图清理任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'final_images_cleanup',
            'status': 'started',
            'details': {}
        }
        
        try:
            # 执行清理（已发货订单，1个月以前）
            cleanup_old_final_images(dry_run=False, days=30)
            log_entry['status'] = 'completed'
            print(f"✅ 效果图清理任务完成")
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['details']['error'] = str(e)
            print(f"❌ 效果图清理任务失败: {e}")
        
        # 保存日志
        self.save_task_log(log_entry)
    
    def setup_schedule(self):
        """设置定时任务"""
        print("⏰ 设置定时任务")
        print("=" * 40)
        
        # 每天凌晨2点执行完整任务（清理+备份）
        if SMART_CLEANUP_AVAILABLE and self.cleanup:
            schedule.every().day.at("02:00").do(self.run_full_task)
        
        # 每天中午12点执行备份任务（备份新清理的文件）
        if BAIDU_BACKUP_AVAILABLE and self.backup:
            schedule.every().day.at("12:00").do(self.run_backup_task)
        
        # 每天凌晨3点执行用户上传原图清理（已发货订单，1个月以前）
        schedule.every().day.at("03:00").do(self.run_uploaded_images_cleanup)
        
        # 每天凌晨3:30执行效果图清理（已发货订单，1个月以前）
        schedule.every().day.at("03:30").do(self.run_final_images_cleanup)
        
        print("✅ 定时任务已设置:")
        if SMART_CLEANUP_AVAILABLE and self.cleanup:
            print("  - 每天 02:00 执行完整任务（清理+备份）")
        if BAIDU_BACKUP_AVAILABLE and self.backup:
            print("  - 每天 12:00 执行备份任务")
        print("  - 每天 03:00 执行用户上传原图清理（已发货订单，1个月以前）")
        print("  - 每天 03:30 执行效果图清理（已发货订单，1个月以前）")
    
    def run_scheduler(self):
        """运行调度器"""
        print("🚀 启动定时任务调度器")
        print("按 Ctrl+C 停止")
        
        self.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n👋 定时任务调度器已停止")
    
    def create_windows_task(self):
        """创建Windows任务计划程序任务"""
        try:
            script_path = os.path.abspath(__file__)
            python_path = sys.executable
            
            # 创建批处理文件
            bat_content = f'''@echo off
cd /d "{os.path.dirname(script_path)}"
"{python_path}" "{script_path}" --run-task
'''
            
            bat_file = "run_cleanup_task.bat"
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write(bat_content)
            
            print(f"✅ 已创建批处理文件: {bat_file}")
            print("\n📋 Windows任务计划程序设置步骤:")
            print("1. 打开'任务计划程序'")
            print("2. 创建基本任务")
            print("3. 触发器: 每天")
            print("4. 开始时间: 02:00")
            print(f"5. 操作: 启动程序 -> {os.path.abspath(bat_file)}")
            print("6. 完成设置")
            
        except Exception as e:
            print(f"创建Windows任务失败: {e}")
    
    def create_linux_cron(self):
        """创建Linux cron任务"""
        try:
            script_path = os.path.abspath(__file__)
            python_path = sys.executable
            
            cron_entry = f"0 2 * * * cd {os.path.dirname(script_path)} && {python_path} {script_path} --run-task"
            
            print("✅ Linux cron任务配置:")
            print("=" * 40)
            print("运行以下命令添加cron任务:")
            print(f"crontab -e")
            print()
            print("添加以下行:")
            print(f"# 每天凌晨2点执行图片清理任务")
            print(f"{cron_entry}")
            print()
            print("保存并退出编辑器")
            
        except Exception as e:
            print(f"创建Linux cron任务失败: {e}")
    
    def show_task_log(self):
        """显示任务日志"""
        try:
            task_log = self.load_task_log()
            
            if not task_log:
                print("📋 任务日志为空")
                return
            
            print(f"📋 任务日志 (最近 {len(task_log)} 条记录):")
            print("-" * 80)
            
            for log in task_log[-10:]:  # 显示最近10条
                timestamp = datetime.fromisoformat(log['timestamp'])
                print(f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"任务类型: {log['task_type']}")
                print(f"状态: {log['status']}")
                
                if log['status'] == 'completed':
                    details = log.get('details', {})
                    if 'cleaned_count' in details:
                        print(f"清理数量: {details['cleaned_count']}")
                    if 'backed_up_count' in details:
                        print(f"备份数量: {details['backed_up_count']}")
                elif log['status'] == 'failed':
                    print(f"错误: {log.get('details', {}).get('error', 'N/A')}")
                
                print("-" * 80)
                
        except Exception as e:
            print(f"显示任务日志失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='定时图片清理任务')
    parser.add_argument('--run-task', action='store_true', help='执行清理任务')
    parser.add_argument('--run-backup', action='store_true', help='执行备份任务')
    parser.add_argument('--run-full', action='store_true', help='执行完整任务')
    parser.add_argument('--run-uploaded-cleanup', action='store_true', help='执行用户上传原图清理任务')
    parser.add_argument('--run-final-cleanup', action='store_true', help='执行效果图清理任务')
    parser.add_argument('--schedule', action='store_true', help='启动定时调度器')
    parser.add_argument('--windows-task', action='store_true', help='创建Windows任务计划程序')
    parser.add_argument('--linux-cron', action='store_true', help='创建Linux cron任务')
    parser.add_argument('--log', action='store_true', help='显示任务日志')
    
    args = parser.parse_args()
    
    task_manager = ScheduledCleanupTask()
    
    if args.run_task:
        task_manager.run_cleanup_task()
    elif args.run_backup:
        task_manager.run_backup_task()
    elif args.run_full:
        task_manager.run_full_task()
    elif args.run_uploaded_cleanup:
        task_manager.run_uploaded_images_cleanup()
    elif args.run_final_cleanup:
        task_manager.run_final_images_cleanup()
    elif args.schedule:
        task_manager.run_scheduler()
    elif args.windows_task:
        task_manager.create_windows_task()
    elif args.linux_cron:
        task_manager.create_linux_cron()
    elif args.log:
        task_manager.show_task_log()
    else:
        print("🕐 定时图片清理任务管理器")
        print("=" * 50)
        print("\n可用命令:")
        print("  --run-task           执行清理任务")
        print("  --run-backup         执行备份任务")
        print("  --run-full           执行完整任务（清理+备份）")
        print("  --run-uploaded-cleanup  执行用户上传原图清理任务")
        print("  --run-final-cleanup     执行效果图清理任务")
        print("  --schedule           启动定时调度器")
        print("  --windows-task 创建Windows任务计划程序")
        print("  --linux-cron   创建Linux cron任务")
        print("  --log          显示任务日志")
        print("\n示例:")
        print("  python scheduled_cleanup.py --run-full")
        print("  python scheduled_cleanup.py --schedule")

if __name__ == '__main__':
    main()




