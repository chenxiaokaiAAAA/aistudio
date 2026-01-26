#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复order_image表，添加is_main字段
"""

import sqlite3
import os

# 数据库路径
db_path = os.path.join('instance', 'pet_painting.db')

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_image'")
    if not cursor.fetchone():
        print("order_image表不存在")
        conn.close()
        exit(1)
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(order_image)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"现有字段: {columns}")
    
    if 'is_main' in columns:
        print("is_main字段已存在，无需添加")
        conn.close()
        exit(0)
    
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
    
    print("is_main字段添加成功！")
    
except Exception as e:
    print(f"修复失败: {e}")
    if 'conn' in locals():
        conn.close()
    exit(1)

