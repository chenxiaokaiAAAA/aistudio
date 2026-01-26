#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为加盟商充值记录表添加赠送金额字段的数据库迁移脚本
运行方法: python add_franchisee_bonus_migration.py
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = 'pet_painting.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件 {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='franchisee_recharges'")
        if not cursor.fetchone():
            print("❌ franchisee_recharges 表不存在，跳过迁移")
            return
        
        # 检查字段是否已经存在
        cursor.execute("PRAGMA table_info(franchisee_recharges)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'bonus_amount' in columns:
            print("✅ bonus_amount 字段已存在，无需迁移")
            return
        
        if 'total_amount' in columns:
            print("✅ total_amount 字段已存在，无需迁移")
            return
        
        # 添加 bonus_amount 字段
        print("正在添加 bonus_amount 字段...")
        cursor.execute("ALTER TABLE franchisee_recharges ADD COLUMN bonus_amount REAL DEFAULT 0.0")
        
        # 添加 total_amount 字段
        print("正在添加 total_amount 字段...")
        cursor.execute("ALTER TABLE franchisee_recharges ADD COLUMN total_amount REAL")
        
        # 更新现有记录，将 total_amount 设置为 amount（兼容旧数据）
        print("正在更新现有充值记录...")
        cursor.execute("UPDATE franchisee_recharges SET total_amount = amount WHERE total_amount IS NULL")
        
        conn.commit()
        print("✅ 数据库迁移成功完成！")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ 数据库迁移失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("加盟商充值赠送功能 - 数据库迁移")
    print("=" * 60)
    print()
    migrate_database()
    print()
    print("迁移完成！请重启服务器使更改生效。")



