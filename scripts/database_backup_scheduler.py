#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库定时备份调度器
支持每日自动备份所有数据库文件到备份目录
"""

import os
import sys
import shutil
import schedule
import time
from datetime import datetime, timedelta
import json

# 数据库文件配置
DATABASE_FILES = [
    'instance/pet_painting.db',
    'pet_painting.db'
]

# 备份目录
BACKUP_DIR = 'instance/backups'

class DatabaseBackupScheduler:
    """数据库备份调度器"""
    
    def __init__(self):
        self.log_file = 'database_backup_log.json'
        self.retention_days = 30  # 保留30天的备份
        
        # 确保备份目录存在
        os.makedirs(BACKUP_DIR, exist_ok=True)
    
    def load_log(self):
        """加载备份日志"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载日志失败: {e}")
        return []
    
    def save_log(self, entry):
        """保存备份日志"""
        try:
            log = self.load_log()
            log.append(entry)
            
            # 只保留最近30天的日志
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            log = [l for l in log if datetime.fromisoformat(l['timestamp']) > cutoff_date]
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存日志失败: {e}")
    
    def backup_database(self, db_path):
        """备份单个数据库文件"""
        if not os.path.exists(db_path):
            print(f"⚠️  数据库文件不存在: {db_path}")
            return None
        
        try:
            # 生成备份文件名（带时间戳和路径标识，避免同名冲突）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            db_name = os.path.basename(db_path)
            
            # 如果路径包含 instance，添加标识
            if 'instance' in db_path.lower():
                backup_name = f"instance_{db_name}.{timestamp}.bak"
            else:
                backup_name = f"root_{db_name}.{timestamp}.bak"
            
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            
            # 复制文件
            shutil.copy2(db_path, backup_path)
            
            # 获取文件大小
            file_size = os.path.getsize(backup_path)
            
            print(f"✅ 备份成功: {backup_name} ({file_size:,} 字节)")
            
            return {
                'backup_name': backup_name,
                'backup_path': backup_path,
                'original_path': db_path,
                'size': file_size,
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"❌ 备份失败 {db_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clean_old_backups(self):
        """清理旧备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            if not os.path.exists(BACKUP_DIR):
                print("ℹ️  备份目录不存在，无需清理")
                return 0
            
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith('.bak'):
                    file_path = os.path.join(BACKUP_DIR, filename)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        # 只删除超过保留期的文件，并且确保不是今天创建的
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            deleted_count += 1
                            print(f"🗑️  删除旧备份: {filename} (创建时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    except Exception as e:
                        print(f"⚠️  处理文件 {filename} 时出错: {e}")
                        continue
            
            if deleted_count > 0:
                print(f"✅ 清理完成，删除了 {deleted_count} 个旧备份文件")
            else:
                print("ℹ️  没有需要清理的旧备份")
                
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理旧备份失败: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run_backup_task(self):
        """执行备份任务"""
        print("=" * 60)
        print(f"🔰 开始执行数据库备份任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'started',
            'backups': [],
            'errors': []
        }
        
        backed_up_count = 0
        total_size = 0
        
        try:
            # 1. 备份所有数据库文件
            for db_path in DATABASE_FILES:
                backup_info = self.backup_database(db_path)
                if backup_info:
                    log_entry['backups'].append(backup_info)
                    backed_up_count += 1
                    total_size += backup_info['size']
            
            # 2. 清理旧备份
            deleted_count = self.clean_old_backups()
            log_entry['deleted_count'] = deleted_count
            
            # 3. 计算备份目录统计信息
            backup_stats = self.get_backup_stats()
            log_entry['backup_stats'] = backup_stats
            
            log_entry['status'] = 'completed'
            log_entry['backed_up_count'] = backed_up_count
            log_entry['total_size'] = total_size
            
            print("\n" + "=" * 60)
            print(f"✅ 备份任务完成")
            print(f"   备份文件数: {backed_up_count}")
            print(f"   总大小: {total_size:,} 字节 ({total_size / 1024 / 1024:.2f} MB)")
            print(f"   删除旧备份: {deleted_count}")
            print(f"   备份目录总文件: {backup_stats['total_files']}")
            print(f"   备份目录总大小: {backup_stats['total_size']:,} 字节 ({backup_stats['total_size'] / 1024 / 1024:.2f} MB)")
            print("=" * 60)
            
        except Exception as e:
            log_entry['status'] = 'failed'
            log_entry['errors'].append(str(e))
            print(f"❌ 备份任务失败: {e}")
        
        # 保存日志
        self.save_log(log_entry)
    
    def get_backup_stats(self):
        """获取备份目录统计信息"""
        total_files = 0
        total_size = 0
        
        try:
            if not os.path.exists(BACKUP_DIR):
                return {
                    'total_files': 0,
                    'total_size': 0
                }
            
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith('.bak'):
                    file_path = os.path.join(BACKUP_DIR, filename)
                    if os.path.exists(file_path):
                        total_files += 1
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            print(f"⚠️  获取统计信息失败: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            'total_files': total_files,
            'total_size': total_size
        }
    
    def show_backup_history(self):
        """显示备份历史"""
        log = self.load_log()
        
        if not log:
            print("📋 暂无备份历史")
            return
        
        print("📋 备份历史（最近20条）:")
        print("=" * 80)
        
        for entry in log[-20:]:
            timestamp = entry['timestamp']
            status = entry['status']
            backed_up = entry.get('backed_up_count', 0)
            total_size = entry.get('total_size', 0)
            
            print(f"\n时间: {timestamp}")
            print(f"状态: {status}")
            print(f"备份文件数: {backed_up}")
            print(f"总大小: {total_size:,} 字节")
            
            if entry.get('errors'):
                print(f"错误: {entry['errors']}")
    
    def setup_schedule(self):
        """设置定时任务"""
        print("⏰ 设置定时备份任务")
        print("=" * 60)
        
        # 每天凌晨3点执行备份
        schedule.every().day.at("03:00").do(self.run_backup_task)
        
        # 每12小时执行一次备份（可选）
        # schedule.every(12).hours.do(self.run_backup_task)
        
        print("✅ 定时任务已设置:")
        print("  - 每天 03:00 执行数据库备份")
        print("  - 自动保留最近 30 天的备份")
        print("  - 备份目录: instance/backups/")
    
    def run_scheduler(self):
        """运行调度器"""
        print("🚀 启动数据库备份调度器")
        print("按 Ctrl+C 停止")
        print()
        
        self.setup_schedule()
        
        # 立即执行一次备份
        print("\n执行首次备份...")
        self.run_backup_task()
        
        print("\n等待定时任务...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n👋 数据库备份调度器已停止")
    
    def create_windows_task_script(self):
        """创建Windows任务计划程序脚本"""
        script_content = f"""@echo off
cd /d {os.path.dirname(os.path.abspath(__file__))}
python database_backup_scheduler.py --run
"""
        
        bat_file = 'run_database_backup.bat'
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 已创建Windows任务脚本: {bat_file}")
        print("\n在Windows任务计划程序中设置:")
        print("  1. 触发器: 每天 03:00")
        print(f"  2. 操作: 启动程序 -> {os.path.abspath(bat_file)}")


def main():
    scheduler = DatabaseBackupScheduler()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--run':
            # 直接执行备份
            scheduler.run_backup_task()
        elif sys.argv[1] == '--schedule':
            # 启动调度器
            scheduler.run_scheduler()
        elif sys.argv[1] == '--history':
            # 显示备份历史
            scheduler.show_backup_history()
        elif sys.argv[1] == '--stats':
            # 显示统计信息
            stats = scheduler.get_backup_stats()
            print("📊 备份统计:")
            print(f"  总文件数: {stats['total_files']}")
            print(f"  总大小: {stats['total_size']:,} 字节 ({stats['total_size'] / 1024 / 1024:.2f} MB)")
        elif sys.argv[1] == '--windows-task':
            # 创建Windows任务脚本
            scheduler.create_windows_task_script()
        else:
            print("使用方法:")
            print("  python database_backup_scheduler.py --run        # 执行一次备份")
            print("  python database_backup_scheduler.py --schedule   # 启动调度器")
            print("  python database_backup_scheduler.py --history    # 查看备份历史")
            print("  python database_backup_scheduler.py --stats      # 查看统计信息")
            print("  python database_backup_scheduler.py --windows-task  # 创建Windows任务脚本")
    else:
        # 默认执行一次备份
        scheduler.run_backup_task()


if __name__ == '__main__':
    main()

