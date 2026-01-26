#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def simple_check_backup(backup_file):
    """简单检查备份数据库"""
    if not os.path.exists(backup_file):
        print(f"❌ 备份文件不存在: {backup_file}")
        return
    
    try:
        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        
        print(f"\n📁 备份文件: {backup_file}")
        print("-" * 40)
        
        # 只获取表名，不执行其他查询
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📋 包含的表: {', '.join(tables)}")
        
        # 只检查重要表的数据量
        important_tables = ['homepage_banner', 'users', 'homepage_config']
        for table in important_tables:
            if table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM '{table}';")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count} 条记录")
                except Exception as e:
                    print(f"   {table}: 检查失败 - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def main():
    backup_files = [
        'instance/pet_painting_backup_20250923_214156.db',
        'instance/pet_painting_backup_20250918_214101.db',
        'instance/pet_painting_backup_20250918_214046.db',
        'instance/pet_painting_backup_20250918_214156.db'
    ]
    
    print("🔍 简单检查备份数据库")
    print("=" * 50)
    
    for backup_file in backup_files:
        simple_check_backup(backup_file)
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
