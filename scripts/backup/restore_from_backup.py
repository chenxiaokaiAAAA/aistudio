#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从备份恢复文件
用于重构出错时恢复代码
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / 'backups' / 'refactor_backups'

def list_backups():
    """列出所有备份"""
    if not BACKUP_DIR.exists():
        return []
    
    backups = []
    for item in BACKUP_DIR.iterdir():
        if item.is_dir() and item.name.startswith('refactor_backup_'):
            info_file = item / 'backup_info.json'
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    backups.append({
                        'timestamp': info['timestamp'],
                        'backup_dir': item,
                        'backup_time': info['backup_time'],
                        'file_count': len(info.get('backed_up_files', []))
                    })
    
    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    return backups


def restore_from_backup(timestamp):
    """从指定备份恢复"""
    backup_path = BACKUP_DIR / f'refactor_backup_{timestamp}'
    
    if not backup_path.exists():
        print(f"[ERROR] 备份不存在: {backup_path}")
        return False
    
    info_file = backup_path / 'backup_info.json'
    if not info_file.exists():
        print(f"[ERROR] 备份信息文件不存在")
        return False
    
    with open(info_file, 'r', encoding='utf-8') as f:
        backup_info = json.load(f)
    
    print("=" * 60)
    print("从备份恢复文件")
    print("=" * 60)
    print(f"备份时间: {backup_info['backup_time']}")
    print(f"备份目录: {backup_path}")
    print()
    
            # 确认恢复
    confirm = input("[WARN] 警告: 这将覆盖当前文件，是否继续? (yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消恢复")
        return False
    
    # 恢复app目录
    backup_app_dir = backup_path / 'app'
    target_app_dir = PROJECT_ROOT / 'app'
    
    if backup_app_dir.exists():
        print("恢复 app 目录...")
        try:
            # 先备份当前app目录（以防万一）
            current_backup = PROJECT_ROOT / 'backups' / f'app_backup_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            if target_app_dir.exists():
                shutil.copytree(target_app_dir, current_backup, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                print(f"  [OK] 当前app目录已备份到: {current_backup}")
            
            # 删除目标目录
            if target_app_dir.exists():
                shutil.rmtree(target_app_dir)
            
            # 恢复备份
            shutil.copytree(backup_app_dir, target_app_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"  [OK] app 目录恢复完成")
        except Exception as e:
            print(f"  [ERROR] app 目录恢复失败: {e}")
            return False
    
    # 恢复关键文件
    key_files = ['start.py', 'test_server.py', 'requirements.txt']
    print()
    print("恢复关键文件...")
    for file_name in key_files:
        backup_file = backup_path / file_name
        target_file = PROJECT_ROOT / file_name
        
        if backup_file.exists():
            try:
                # 备份当前文件
                if target_file.exists():
                    current_backup_file = PROJECT_ROOT / 'backups' / f'{file_name}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    shutil.copy2(target_file, current_backup_file)
                
                # 恢复文件
                shutil.copy2(backup_file, target_file)
                print(f"  [OK] {file_name} 恢复完成")
            except Exception as e:
                print(f"  [ERROR] {file_name} 恢复失败: {e}")
        else:
            print(f"  [WARN] {file_name} 在备份中不存在，跳过")
    
    print()
    print("=" * 60)
    print("[OK] 恢复完成")
    print("=" * 60)
    print()
    print("[重要提示]")
    print("  1. 文件已从备份恢复")
    print("  2. 当前文件已备份到 backups/ 目录")
    print("  3. 请检查恢复的文件是否正确")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从备份恢复文件')
    parser.add_argument('timestamp', nargs='?', help='备份时间戳（格式: YYYYMMDD_HHMMSS）')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--latest', action='store_true', help='恢复最新备份')
    
    args = parser.parse_args()
    
    if args.list or (not args.timestamp and not args.latest):
        backups = list_backups()
        if backups:
            print("=" * 60)
            print("可用备份列表")
            print("=" * 60)
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['timestamp']}")
                print(f"   时间: {backup['backup_time']}")
                print(f"   文件数: {backup['file_count']}")
                print()
            print("使用方法:")
            print("  python scripts/backup/restore_from_backup.py <timestamp>")
            print("  或")
            print("  python scripts/backup/restore_from_backup.py --latest")
        else:
            print("没有找到备份")
        return
    
    if args.latest:
        backups = list_backups()
        if backups:
            timestamp = backups[0]['timestamp']
            restore_from_backup(timestamp)
        else:
            print("没有找到备份")
    elif args.timestamp:
        restore_from_backup(args.timestamp)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
