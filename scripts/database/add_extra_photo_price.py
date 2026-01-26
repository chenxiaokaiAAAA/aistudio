#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加 extra_photo_price 字段到 products 表
"""
import sqlite3
import os
import sys

# 获取脚本所在目录的父目录（aistudio目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
aistudio_dir = os.path.dirname(os.path.dirname(script_dir))  # 回到aistudio目录
project_root = os.path.dirname(aistudio_dir)  # 回到项目根目录

# 尝试多个可能的数据库路径（按优先级排序）
db_paths = [
    os.path.join(aistudio_dir, 'instance', 'pet_painting.db'),  # aistudio/instance/pet_painting.db
    os.path.join(project_root, 'instance', 'pet_painting.db'),   # 项目根目录/instance/pet_painting.db
    os.path.join(aistudio_dir, 'pet_painting.db'),              # aistudio/pet_painting.db
    os.path.join(project_root, 'pet_painting.db'),             # 项目根目录/pet_painting.db
]

db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("ERROR: Cannot find database file")
    print("Tried paths:", db_paths)
    exit(1)

print(f"Using database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查字段是否已存在
cursor.execute("PRAGMA table_info(products)")
columns = [row[1] for row in cursor.fetchall()]

if 'extra_photo_price' in columns:
    print("=" * 50)
    print("OK: Field 'extra_photo_price' already exists")
    print("=" * 50)
    
    # 显示一些示例数据
    cursor.execute("SELECT id, name, free_selection_count, extra_photo_price FROM products LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        print("\nSample data:")
        for row in rows:
            print(f"  Product ID {row[0]}: {row[1]}")
            print(f"    free_selection_count: {row[2]}")
            print(f"    extra_photo_price: {row[3]}")
else:
    print("=" * 50)
    print("Adding field 'extra_photo_price'...")
    cursor.execute("ALTER TABLE products ADD COLUMN extra_photo_price REAL DEFAULT 10.0")
    cursor.execute("UPDATE products SET extra_photo_price = 10.0 WHERE extra_photo_price IS NULL")
    conn.commit()
    print("OK: Field added successfully!")
    print("=" * 50)
    
    # 验证添加结果
    cursor.execute("PRAGMA table_info(products)")
    columns_after = [row[1] for row in cursor.fetchall()]
    if 'extra_photo_price' in columns_after:
        print("VERIFIED: Field 'extra_photo_price' is now in the database")
    else:
        print("ERROR: Field was not added properly!")

conn.close()
