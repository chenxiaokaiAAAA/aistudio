# -*- coding: utf-8 -*-
"""
直接添加退款申请相关字段到orders表（不导入test_server）
"""
import sqlite3
import os
import sys

# 数据库文件路径 - 尝试多个可能的位置
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
    print(f"[ERROR] 数据库文件不存在，尝试过的路径:")
    for path in possible_paths:
        print(f"  - {path}")
    sys.exit(1)

if not os.path.exists(db_path):
    print(f"[ERROR] 数据库文件不存在: {db_path}")
    sys.exit(1)

print(f"正在连接数据库: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(orders)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"当前orders表的字段: {', '.join(columns)}")
    
    # 需要添加的字段
    fields_to_add = [
        ('refund_request_reason', 'TEXT'),
        ('refund_request_time', 'DATETIME'),
        ('refund_request_status', 'VARCHAR(20)')
    ]
    
    for field_name, field_type in fields_to_add:
        if field_name not in columns:
            try:
                sql = f"ALTER TABLE orders ADD COLUMN {field_name} {field_type}"
                cursor.execute(sql)
                print(f"[OK] 已添加字段: {field_name}")
            except Exception as e:
                print(f"[WARN] 添加字段 {field_name} 失败: {e}")
        else:
            print(f"[INFO] 字段 {field_name} 已存在，跳过")
    
    conn.commit()
    print("[OK] 退款申请字段添加完成！")
    
    conn.close()
    
except Exception as e:
    print(f"[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
