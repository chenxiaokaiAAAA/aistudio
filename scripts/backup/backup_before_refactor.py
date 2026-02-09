#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构前自动备份脚本
在代码重构前自动创建备份，防止数据丢失
"""

import os
import sys
import shutil
import json
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / 'backups' / 'refactor_backups'
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
CURRENT_BACKUP_DIR = BACKUP_DIR / f'refactor_backup_{TIMESTAMP}'

# 需要备份的目录和文件
BACKUP_PATTERNS = [
    'app/routes/**/*.py',  # 所有路由文件
    'app/services/**/*.py',  # 所有服务文件
    'app/utils/**/*.py',  # 所有工具文件
    'app/__init__.py',  # 应用初始化文件
    'app/models.py',  # 模型文件
]

def create_backup():
    """创建备份"""
    print("=" * 60)
    print("代码重构前备份工具")
    print("=" * 60)
    print()
    
    # 创建备份目录
    CURRENT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"备份目录: {CURRENT_BACKUP_DIR}")
    print()
    
    # 备份文件列表
    backed_up_files = []
    skipped_files = []
    
    # 备份app目录
    app_dir = PROJECT_ROOT / 'app'
    if app_dir.exists():
        backup_app_dir = CURRENT_BACKUP_DIR / 'app'
        print(f"备份 app 目录...")
        try:
            shutil.copytree(app_dir, backup_app_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            backed_up_files.append('app/')
            print(f"  [OK] app 目录备份完成")
        except Exception as e:
            print(f"  [ERROR] app 目录备份失败: {e}")
            skipped_files.append('app/')
    
    # 备份关键文件
    key_files = [
        'start.py',
        'test_server.py',
        'requirements.txt',
    ]
    
    print()
    print("备份关键文件...")
    for file_name in key_files:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            try:
                backup_file = CURRENT_BACKUP_DIR / file_name
                shutil.copy2(file_path, backup_file)
                backed_up_files.append(file_name)
                print(f"  [OK] {file_name} 备份完成")
            except Exception as e:
                print(f"  [ERROR] {file_name} 备份失败: {e}")
                skipped_files.append(file_name)
        else:
            skipped_files.append(file_name)
            print(f"  [WARN] {file_name} 不存在，跳过")
    
    # 保存备份信息
    backup_info = {
        'timestamp': TIMESTAMP,
        'backup_dir': str(CURRENT_BACKUP_DIR),
        'backed_up_files': backed_up_files,
        'skipped_files': skipped_files,
        'backup_time': datetime.now().isoformat()
    }
    
    info_file = CURRENT_BACKUP_DIR / 'backup_info.json'
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(backup_info, f, ensure_ascii=False, indent=2)
    
    # 计算备份大小
    total_size = 0
    for root, dirs, files in os.walk(CURRENT_BACKUP_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    
    total_size_mb = total_size / (1024 * 1024)
    
    print()
    print("=" * 60)
    print("备份完成")
    print("=" * 60)
    print(f"备份目录: {CURRENT_BACKUP_DIR}")
    print(f"备份文件数: {len(backed_up_files)}")
    print(f"跳过文件数: {len(skipped_files)}")
    print(f"备份大小: {total_size_mb:.2f} MB")
    print()
    print("备份信息已保存到: backup_info.json")
    print()
    print("[重要提示]")
    print("  1. 备份已创建，可以安全进行重构")
    print("  2. 如果重构出错，可以使用以下命令恢复:")
    print(f"     python scripts/backup/restore_from_backup.py {TIMESTAMP}")
    print("  3. 或手动从备份目录恢复文件")
    print("=" * 60)
    
    return CURRENT_BACKUP_DIR, backup_info


def list_backups():
    """列出所有备份"""
    if not BACKUP_DIR.exists():
        print("没有找到备份目录")
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
                        'backup_dir': str(item),
                        'backup_time': info['backup_time'],
                        'file_count': len(info.get('backed_up_files', []))
                    })
    
    # 按时间排序（最新的在前）
    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return backups


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='代码重构前备份工具')
    parser.add_argument('--backup', action='store_true', help='创建备份')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--cleanup', type=int, help='清理N天前的备份（保留最近N天）')
    
    args = parser.parse_args()
    
    if args.list:
        backups = list_backups()
        if backups:
            print("=" * 60)
            print("备份列表")
            print("=" * 60)
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['timestamp']}")
                print(f"   时间: {backup['backup_time']}")
                print(f"   文件数: {backup['file_count']}")
                print(f"   目录: {backup['backup_dir']}")
                print()
        else:
            print("没有找到备份")
        return
    
    if args.cleanup:
        # 清理旧备份
        backups = list_backups()
        cutoff_date = datetime.now().timestamp() - (args.cleanup * 24 * 3600)
        deleted_count = 0
        for backup in backups:
            backup_time = datetime.fromisoformat(backup['backup_time']).timestamp()
            if backup_time < cutoff_date:
                backup_path = Path(backup['backup_dir'])
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    deleted_count += 1
                    print(f"删除旧备份: {backup['timestamp']}")
        print(f"清理完成，删除了 {deleted_count} 个旧备份")
        return
    
    # 默认创建备份
    create_backup()


if __name__ == '__main__':
    main()
