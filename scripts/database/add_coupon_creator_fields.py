# -*- coding: utf-8 -*-
"""
添加优惠券创建人字段到Coupon表
"""
import sqlite3
import os
import sys

# 数据库文件路径
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'pet_painting.db'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'pet_painting.db'),
    'pet_painting.db',
    os.path.join(os.getcwd(), 'pet_painting.db'),
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print(f"[ERROR] 数据库文件不存在")
    sys.exit(1)

print(f"正在连接数据库: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(coupons)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 添加创建人字段
    if 'franchisee_id' not in columns:
        cursor.execute("ALTER TABLE coupons ADD COLUMN franchisee_id INTEGER")
        print("[OK] 添加 franchisee_id 字段成功")
    else:
        print("[INFO] franchisee_id 字段已存在")
    
    if 'staff_user_id' not in columns:
        cursor.execute("ALTER TABLE coupons ADD COLUMN staff_user_id INTEGER")
        print("[OK] 添加 staff_user_id 字段成功")
    else:
        print("[INFO] staff_user_id 字段已存在")
    
    if 'creator_type' not in columns:
        cursor.execute("ALTER TABLE coupons ADD COLUMN creator_type VARCHAR(20) DEFAULT 'system'")
        print("[OK] 添加 creator_type 字段成功")
    else:
        print("[INFO] creator_type 字段已存在")
    
    if 'creator_name' not in columns:
        cursor.execute("ALTER TABLE coupons ADD COLUMN creator_name VARCHAR(100)")
        print("[OK] 添加 creator_name 字段成功")
    else:
        print("[INFO] creator_name 字段已存在")
    
    conn.commit()
    conn.close()
    print("[OK] 完成！")
    
except Exception as e:
    print(f"[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
