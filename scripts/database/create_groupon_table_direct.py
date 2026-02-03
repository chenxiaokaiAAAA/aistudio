# -*- coding: utf-8 -*-
"""
直接创建团购套餐配置表（不导入test_server）
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
    
    # 检查表是否已存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='groupon_packages'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        print("[INFO] 表 groupon_packages 已存在，跳过创建")
    else:
        # 创建表
        create_table_sql = """
        CREATE TABLE groupon_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform VARCHAR(50) NOT NULL,
            package_name VARCHAR(100) NOT NULL,
            package_amount FLOAT NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, package_name)
        )
        """
        cursor.execute(create_table_sql)
        print("[OK] 表 groupon_packages 创建成功！")
    
    conn.commit()
    conn.close()
    print("[OK] 完成！")
    
except Exception as e:
    print(f"[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
