#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复所有数据库文件中的order_image表，添加is_main字段
"""

import sqlite3
import os

# 所有可能的数据库路径
possible_paths = [
    'pet_painting.db',
    os.path.join('instance', 'pet_painting.db'),
    os.path.join('instance', 'database.db'),
    'database.db'
]

def fix_database(db_path):
    """修复单个数据库文件"""
    if not os.path.exists(db_path):
        return False, f"文件不存在: {db_path}"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_image'")
        if not cursor.fetchone():
            conn.close()
            return False, f"order_image表不存在: {db_path}"
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(order_image)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_main' in columns:
            conn.close()
            return True, f"is_main字段已存在: {db_path}"
        
        # 添加is_main字段
        print(f"正在为 {db_path} 添加is_main字段...")
        cursor.execute("ALTER TABLE order_image ADD COLUMN is_main BOOLEAN DEFAULT 0 NOT NULL")
        
        # 对于已有数据，将第一条图片设为主图（兼容旧数据）
        cursor.execute("""
            UPDATE order_image 
            SET is_main = 1 
            WHERE id IN (
                SELECT MIN(id) 
                FROM order_image 
                GROUP BY order_id
            )
        """)
        
        conn.commit()
        conn.close()
        
        return True, f"is_main字段添加成功: {db_path}"
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return False, f"修复失败 {db_path}: {e}"

if __name__ == '__main__':
    print("=" * 60)
    print("开始修复所有数据库文件中的order_image表")
    print("=" * 60)
    
    success_count = 0
    for db_path in possible_paths:
        success, message = fix_database(db_path)
        print(message)
        if success:
            success_count += 1
    
    print("=" * 60)
    print(f"修复完成！成功处理 {success_count} 个数据库文件")
    print("=" * 60)

