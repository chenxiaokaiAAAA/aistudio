#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为OrderImage表添加is_main字段
"""

import sqlite3
import os
import sys
from datetime import datetime

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def add_is_main_field():
    """为order_image表添加is_main字段"""
    # 尝试多个可能的数据库路径
    possible_paths = [
        'pet_painting.db',
        os.path.join('instance', 'pet_painting.db'),
        os.path.join('instance', 'database.db'),
        'database.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print(f"未找到数据库文件，尝试过的路径: {possible_paths}")
        return False
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_image'")
        if not cursor.fetchone():
            print("order_image表不存在，将在应用启动时自动创建")
            conn.close()
            return True
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(order_image)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_main' in columns:
            print("is_main字段已存在，跳过迁移")
            conn.close()
            return True
        
        # 添加is_main字段
        print("正在添加is_main字段...")
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
        
        print("is_main字段添加成功")
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("开始迁移：为OrderImage表添加is_main字段")
    print("=" * 50)
    
    if add_is_main_field():
        print("\n迁移完成！")
    else:
        print("\n迁移失败！")

